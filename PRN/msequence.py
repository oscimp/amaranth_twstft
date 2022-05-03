from math import log2, ceil


####################
#		Following 
#		http://www-math.ucdenver.edu/~wcherowi/courses/m5410/m5410fsr.html
#		https://www.gaussianwaves.com/2018/09/maximum-length-sequences-m-sequences/
#		https://en.wikipedia.org/wiki/Primitive_polynomial_(field_theory)
#		https://www.cs.miami.edu/home/burt/learning/Csc609.022/random_numbers.html
#		https://liquidsdr.org/doc/msequence/
#		
#		
#		to define good taps that will generate a maximum length N bits sequence,
#		we should provide them in accordance to a primitive polynomials 
#		of degree N with coefficients in GF(2).
#		These are the polynomials which generate the whole set of 
#		non-zero polynomials of degree less than N of coefficients in GF(2) 
#		when raised to the power x in [0,2^N-1].
#		These polynomials have a certain characteristic :
#			They are irreducibles
#		
#		As it is hard to prove such polynomials are irreducibles,
#		we will prefer to try every potential taps positions for our LFSR 
#		and generate their associated pseudo-random sequence to see if their period 
#		is equal to 2^n-1 
#
#		Example of LFSR representative polynomial: 
#			X⁶ + X⁴ + X + 1 is representative of a 6-bits LFSR with taps on 
#			bits 0, 1 and 4.
#			As the nth coefficient is not representative of 
#			any tap in the implementation of the LFSR, 
#			we will omit it on purpose when generating the taps
#			
####################

def unary_xor(x):
	"""if x == 0b0101101, returns 0^1^0^1^1^0^1"""
	res = x & 1
	for i in range(1,int.bit_length(x)):
		x=x>>1
		res ^= 1 & x
	return res

def next(current, taps,bit_len):
	"""returns the next state of the LFSR 
	following its size(bit_len), the taps 
	(taps) and its current state (current)"""
	bit = unary_xor(current & taps)
	res = current >> 1
	res |= bit << (bit_len-1)
	return res

def m_seq_taps(bit_len, limit = 10):
	"""generates (limit) taps which binary values 
	represent where to put the taps on an LFSR to 
	generate a m-sequence of (bit_len) bits values
	
	Parameters
    ----------
    bit_len : greater than 1 integer
		the number of bits for our m-sequence generator
	
	limit : positive integer
		the maximum number of different taps we want to get
	
	----------
	returns a list of taps
	
	"""
	taps = []
	first = 0x1
	
	#we only test odd numbers as the constant coefficient 
	#of a primitive polynomial should always be 1 
	#otherwise we could divide the polynomial by X (and primitive polynomials are irreducibles)
	# + there is
	#no need to test polynomials of degree n because the nth coefficient
	#doesn't correspond to any tap
	taps_to_test = [2*i +1 for i in range(ceil(pow(2,bit_len)/2))]
	for taps in taps_to_test:
		test = first
		
		for j in range((pow(2,bit_len)-2)) : 
			test = next(test, taps, bit_len)
			
			if (test == first or test == 0):
				break
			
			
		if (test != first and test !=0):
			#print(f"sequence with taps {taps} is a m-sequence")
			taps.append(taps)
			limit-=1
			if limit == 0 :
				break
	return taps

def test_mseq(taps, bit_len, iterations = 0):
	"""checks if (taps) can be used as m-sequence taps for our LFSR
	
	Parameters
    ----------
    taps : odd positive integer
		the integer representation of the taps we want to check
	
	"""
	 
	if iterations <= 0 :
		iterations = pow(2,bit_len)
	
	vector = 1
	test = vector
	for i in range(iterations):
		vector = next(vector,taps,bit_len)
		assert vector != 0
		assert (i != pow(2,bit_len)-2) or (vector ==1)
		assert (i == pow(2,bit_len)-2) or (vector !=1)
	taps = bin(taps)
	print(f"{taps} can be used as taps for a pseudo-random generator for a {bit_len} bits LFSR")