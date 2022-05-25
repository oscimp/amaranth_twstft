#!/usr/bin/env python3

from amaranth import *
from math import log


class GlobalCounter(Elaboratable):
	"""A module that outputs 1 as long as it hasn't counted up to its max_val.
	Otherwise, outputs 0 until it is resetted.
	
    Parameters
    ----------
    counter_width :positive integer
    	number of bits to use for the counter
    
    max_val : positive integer
    	the counter counts up to this value
    
    Attributes
    ----------
    
    counter_width :positive integer
    	number of bits to use for the counter
    
    max_val : positive integer
    	the counter counts up to this value
    	
	output : Signal()
		the output of the counter
	
	reset : Signal()
		input signal to restart the counter
		
	tick : Signal()
		input signal driving the counter speed
	
	counter : Signal(counter_width)
		the value of the counter
	
	
    """
	def __init__(self, counter_width, max_val):
		assert max_val < pow(2,counter_width)
		self._counter_width = counter_width
		self._max_val = max_val
		self.reset = Signal()
		self.tick = Signal()
		self.output = Signal()
		if self._max_val < 0 :
			self._max_val = pow(2,counter_width)
		self.counter = Signal(self._counter_width, reset=0, name="globalCounter")
		
	def elaborate(self, platform):
		m = Module()
		with m.If(self.counter == self._max_val):
				m.d.sync += self.output.eq(0)
		with m.Else():
			m.d.sync += [
				self.output.eq(1),
			]
			with m.If(self.tick):
				m.d.sync += self.counter.eq(self.counter + 1)
		with m.If(self.reset):
			m.d.sync += self.counter.eq(0)
			
		return m
