from enum import Enum
from amaranth import Cat, Module, Shape, Signal
from amaranth.lib.wiring import Component, In, Out

TIMECODE_SIZE = 6

class TimeCoderMode(Enum):
    OFF = 0
    INVERT_FIRST_CODE = 1
    TIMECODE = 2 # also invert first code

class TimeCoder(Component):
    mode: In(Shape.cast(TimeCoderMode))

    set_time: In(1)
    time: In(TIMECODE_SIZE)

    pps: In(1)
    next_bit: In(1)

    data: Out(1)

    def elaborate(self, platform):
        m = Module()

        time = Signal(TIMECODE_SIZE)
        shift_time = Signal(TIMECODE_SIZE + 1)

        with m.If(self.mode != TimeCoderMode.OFF):
            m.d.comb += self.data.eq(shift_time[0])

        with m.If(self.next_bit):
            m.d.sync += shift_time.eq(shift_time.shift_right(1))

        with m.If(self.pps):
            next_time = Signal.like(time)
            with m.If(time == 60 -1):
                m.d.comb += next_time.eq(0)
            with m.Else():
                m.d.comb += next_time.eq(time + 1)
            m.d.sync += time.eq(next_time)
            with m.If(self.mode == TimeCoderMode.TIMECODE):
                m.d.sync += shift_time.eq(Cat(1, next_time))
            with m.Else():
                m.d.sync += shift_time.eq(1)

        with m.If(self.set_time):
            m.d.sync += time.eq(self.time)

        return m
