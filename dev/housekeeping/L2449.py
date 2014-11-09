# Dominik Gothe
# gothed [magic email symbol] pha.jhu.edu
# Python 2.7


#class MalformedADCPacket(Exception):
#		pass

# The LTC2449 class is responsible for converting the ADC data to a voltage.
# The LTC2449 is a Linear Technology 24 bit ADC with 16 muxed channels and one common.
# The ADC word (four bytes) is the raw bit output produced by the ADC.
class L2449:
	mal = False # A maleformedADCPacket flag
	# Optional __init__ to define comm and vref
	def __init__(self, comm=2.048, vref=4.096):
		try:
			self.comm = float( comm ) # Voltage of COM pin, in Volts
			self.vref = float( vref ) # Voltage of VREF pin, in Volts
		except Exception, e:
			self.comm = 2.048
			self.vref = 4.096
			print "VREF or COMM is bad. Default to COMM=2.048 and VREF=4.096.", e
			
	# See LTC2449 Datasheet for ADC word format
	def translate(self, word):
		mal = False # A maleformedADCPacket flag
		EOC = bool( word & 0x80000000 ) # End Of Conversion bit
		DMY = bool( word & 0x40000000 ) # Dummy bit
		SIG = bool( word & 0x20000000 ) # Sign bit
		MSB = bool( word & 0x10000000 ) # Most Significant Bit
		sample = word & 0x0FFFFFFF      # Actual ADC sample
		voltage = 666                   # Voltage of 666 indicates MalformedADCPacket
	 
		if EOC:
			mal = True
			voltage = 666	
		#raise MalformedADCPacket("End of Conversion bit is not zero")
	 
		if DMY:
			mal = True
			voltage = 777	
		#raise MalformedADCPacket("Dummy bit is not zero")
	 
		if SIG == MSB:
			mal = True
			voltage = 888	
		#raise MalformedADCPacket("ADC is Clipping: OverUnder")
			
		if not SIG:
			sample = 0x10000000 - sample
			sample = -sample
		
		if not mal:
			voltage = sample/float(0x10000000)*self.vref*.5 + self.comm # Actual voltage value
			
		return voltage
