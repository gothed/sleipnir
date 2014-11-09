# Dominik Gothe
# gothed [magic email symbol] pha.jhu.edu
# Python 2.7

import struct

#
# This class has knowledge of the specific hardware layout of "sleipnir".
# It is capable of identifying which ADC send the data as well as the ADC channel.
class sleip:
	INP = 255 # Stores the postivie input channel.
	INM = 255 # Stores the negative input channel.
	index = 0 # Stores the ADC index, used as adcs[index].
	word = 0  # Stores teh ADC word.
	
	# Non optional init to pass along the adcs.
	# progmem is optional; check via "if progmem is not None".
	def __init__(self, adcs, progmem=None):
		self.adcs    = adcs
		self.progmem = progmem
	
	# This function unpacks a data packet.
	# See extract_status for information regarding ADC status.
	# The ADC word is the raw digital output from the ADC.
	def unpack(self, packet):
		(status, self.word) = struct.unpack_from(">BI", packet)
		self.extract_status(status)
		
	# This function determins which ADC is talking and what channel is being read.
	# Sleipnir channel encoding follows the Linear Technology format.
	# See LTC2449 data sheet page 12 for details.
	def extract_status(self, status):
		self.index = status >> 5							# Which ADC is talking
		SGL 	= bool( status & 0b00010000 ) 	# Single Ended Measurment or Bipolar
		ODD 	= bool( status & 0b00001000 ) 	# Odd channel?
		a210	= status & 0b00000111 		      # LTC Adress A2,A1, and A0
		
		if SGL:
			self.INP = a210 * 2 + ODD
			self.INM = "COM"
			
		else:
			self.INP = a210 * 2 + (not ODD)
			self.INM = a210 * 2 + ODD
	
	def extract_value(self, packet):
		self.unpack(packet)
		return [self.index,self.INP,self.INM, self.adcs[self.index-1].translate(self.word)]
