from amaranth import ClockDomain, ClockSignal, Instance, Module, Mux, ResetSignal, Signal
from amaranth.lib.wiring import Component, In, Out

from amaranth_twstft.safe_timer import SafeTimer


class Clocking(Component):
    pps_in: In(1)
    clk10_in: In(1)

    pps: Out(1)
    delayed_pps: Out(1)
    pps_phase: Out(5, reset=31)

    # flags
    auto_calibrate: In(1)
    ask_calibrate: In(1)
    calibration_finish: Out(1)
    pps_good: Out(1)
    pps_late: Out(1)
    pps_early: Out(1)
    lost_lock: Out(1)

    def elaborate(self, platform):
        m = Module()

        mmcm_feedback = Signal()
        mmcm_locked = Signal()
        mmcm_sync = Signal()
        mmcm_clk210 = Signal()
        mmcm_clk10 = Signal()
        m.submodules.mmcm = Instance(
                'MMCME2_ADV',
                p_CLKFBOUT_MULT_F = 63,
                p_CLKIN1_PERIOD = 100,
                p_CLKOUT0_DIVIDE_F = 2.25,
                p_CLKOUT1_DIVIDE = 3,
                p_CLKOUT2_DIVIDE = 63, # restituate the 10MHz clock, safely readable from the 280MHz clock domain
                p_CLKOUT2_PHASE = -180.0/28,

                i_CLKFBIN = mmcm_feedback,
                o_CLKFBOUT = mmcm_feedback,
                i_CLKINSEL = 1,
                o_LOCKED = mmcm_locked,

                i_CLKIN1 = self.clk10_in,
                o_CLKOUT0 = mmcm_sync,
                o_CLKOUT1 = mmcm_clk210,
                o_CLKOUT2 = mmcm_clk10,

                # Unused inputs tied to zero
                i_CLKIN2 = 0,
                i_DADDR = 0,
                i_DCLK = 0,
                i_DEN = 0,
                i_DI = 0,
                i_DWE = 0,
                i_PSCLK = 0,
                i_PSEN = 0,
                i_PSINCDEC = 0,
                i_PWRDWN = 0,
                i_RST = 0,
                )
        m.submodules += Instance(
                'BUFG',
                i_I = mmcm_sync,
                o_O = ClockSignal('sync'),
                )
        m.d.comb += self.lost_lock.eq(~mmcm_locked)

        delay_reset = Signal() # forcibly reset the delay element
        delay_ready = Signal() # is asserted when the delay element is ready
        m.submodules += Instance(
                'IDELAYCTRL',
                o_RDY = delay_ready,
                i_REFCLK = mmcm_clk210,
                i_RST = ResetSignal('sync') | delay_reset,
                )
        delay_cnt = Signal(5)
        delay_load = Signal()
        m.submodules += Instance(
                'IDELAYE2',
                p_DELAY_SRC = 'IDATAIN',
                p_HIGH_PERFORMANCE_MODE = 'TRUE',
                p_IDELAY_TYPE = 'VAR_LOAD',
                p_REFCLK_FREQUENCY = 210.0,

                i_C = ClockSignal('sync'),
                i_IDATAIN = self.pps_in,
                o_DATAOUT = self.delayed_pps,
                i_CNTVALUEIN = delay_cnt,
                i_LD = delay_load,
                i_CE = 0,# delay_inc,

                i_DATAIN = 0,
                i_CINVCTRL = 0,
                i_INC = 1,
                i_LDPIPEEN = 0,
                i_REGRST = 0,
                )

        # synchronisation chain
        a = Signal()
        b = Signal()
        c = Signal()

        m.d.sync += a.eq(self.delayed_pps)
        m.d.sync += b.eq(a)
        m.d.sync += c.eq(b)

        pps_detected = Signal()
        m.d.comb += pps_detected.eq(b & ~c)

        m.submodules.timer = timer = SafeTimer(int(280e6)-1) # minus one because we need one tick to reset
        m.d.comb += timer.tick.eq(True)

        with m.If(timer.finished & pps_detected):
            m.d.comb += self.pps_good.eq(True)
            m.d.comb += timer.reset.eq(True)
        with m.Elif(pps_detected):
            m.d.comb += self.pps_early.eq(True)
            m.d.comb += timer.reset.eq(True)
        with m.Elif(timer.finished):
            m.d.comb += self.pps_late.eq(True)
            m.d.comb += timer.reset.eq(True)

        m.d.sync += delay_load.eq(False)

        calibration_done = Signal()
        calibration_asked = Signal()
        with m.If(self.ask_calibrate):
            m.d.sync += calibration_asked.eq(True)

        with m.FSM(reset='START'):
            with m.State('START'):
                with m.If(self.auto_calibrate):
                    m.next = 'CALIBRATION_BEGIN'
                with m.Else():
                    m.next = 'RUNNING'

            with m.State('RUNNING'):
                with m.If(calibration_asked):
                    m.d.sync += calibration_asked.eq(False)
                    with m.If(calibration_done):
                        m.next = 'FINALIZE'
                    with m.Else():
                        m.next = 'CALIBRATION_BEGIN'
                with m.If(self.pps_late | self.pps_early):
                    m.d.sync += calibration_done.eq(False)
                    with m.If(self.auto_calibrate):
                        m.next = 'CALIBRATION_BEGIN'
                with m.Else():
                    m.d.comb += self.pps.eq(pps_detected)

            with m.State('CALIBRATION_BEGIN'):
                m.d.sync += delay_cnt.eq(0)
                m.d.sync += delay_load.eq(True)
                m.d.sync += calibration_done.eq(False)
                m.d.sync += self.pps_phase.eq(31)
                m.next = 'CALIBRATION'

            with m.State('CALIBRATION'):
                with m.If(self.pps_good):
                    with m.If(delay_cnt == 31): # no jumps have been found in the whole span
                        m.d.sync += delay_cnt.eq(15) # set delay to the middle value
                        m.d.sync += delay_load.eq(True)
                        m.next = 'FINALIZE'
                    with m.Else():
                        m.d.sync += delay_cnt.eq(delay_cnt + 1) # step to next delay
                        m.d.sync += delay_load.eq(True)
                with m.If(self.pps_late): # the step made us cross the metastablility zone
                    delay_step = 1/(2*32*210e6)
                    periode = 1/280e6
                    steps_for_half_periode = round(periode / delay_step / 2)
                    m.d.sync += delay_cnt.eq( # choose the delay the farthest possible from the metastablility
                            Mux(delay_cnt > 15,
                                Mux(delay_cnt > steps_for_half_periode,
                                    delay_cnt - steps_for_half_periode,
                                    0),
                                Mux(delay_cnt < 31 - steps_for_half_periode,
                                    delay_cnt + steps_for_half_periode,
                                    31)))
                    m.d.sync += delay_load.eq(True)
                    m.next = 'FINALIZE'

            with m.State('FINALIZE'):
                with m.If(self.pps_good):
                    m.d.comb += self.pps.eq(True)
                    m.d.sync += calibration_done.eq(True)
                    m.d.comb += self.calibration_finish.eq(True)
                    m.next = 'RUNNING'

        edge_detect_10_a = Signal()
        edge_detect_10_b = Signal()
        m.d.sync += edge_detect_10_a.eq(mmcm_clk10)
        m.d.sync += edge_detect_10_b.eq(edge_detect_10_a)
        phase_count = Signal(5)
        with m.If(edge_detect_10_a & ~edge_detect_10_b):
            m.d.sync += phase_count.eq(0)
        with m.Else():
            m.d.sync += phase_count.eq(phase_count + 1)
        with m.If(self.pps):
            m.d.sync += self.pps_phase.eq(phase_count)

        return m
