# Dominik Gothe
# gothed [magic email symbol] pha.jhu.edu
# Parent Project: Beefy Miracle
# 07/30/2014
# Python 2.7

# Relies on external PySerial
# Relies on external PyRo

# Fix Python Path
import sys
sys.path.append('/mnt/alfheim/SpiderOak/BeefyMiracle/housekeeping')

# Beefy Classes
import dirio
import insio
import sleip
import L2449
import DT670

# Standard Python Classes
import threading
import time
import datetime
import os
import socket

# PyRo
import Pyro4

# We have to import this to deal with the shortcomeings of dirfiles!
from math import isnan
import struct


class Odin(object):

	def __init__(self, datapath, confpath, currentpath, serpath='/dev/ttyUSB1', baud=1250000): 
		# This even signals all threads to shutdown gracefully
		self.shutdown = threading.Event()
		self.shutdown.clear()
		
		# This is the file IO class
			
		# (Shutdown Event, autostart, data record path, configuration file path)
		self.io = dirio.dirio(self.shutdown, False, datapath, confpath, currentpath, 600)
		
		# This is the instrumen's data IO port
		# (Shutdown Event, Autostart, Serial Port, baud rate, COBS packet size)
		self.instio = insio.insio(self.shutdown, False, serpath, baud, 7)
		
		# These represent the two physical ADCs living inside sleipnir
		# (VCOM, VREF)
		self.adc1 = L2449.L2449(2.048, 4.096)
		self.adc2 = L2449.L2449(2.048, 4.096)
		
		# This represents the diode read out system code named "Sleipnir"
		self.sleipnir = sleip.sleip((self.adc1,self.adc2))
		
		# Clear VCP buffers
		self.instio.clearBuffers()
			
	# In this function the gnomes acuire a single measurment
	def acquire_data(self):
		print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: Odin [Status]: All seven dwarfs are out mining.'
		while not self.shutdown.is_set():
			while not self.instio.pktque.empty():
				# Find retrive a valid and decoded packet from the instrument IO stream
				# We keep track of the packet and receive time
				try:
					(packet, RXtime) = self.instio.decodePacket()
				except insio.MalformedPacket, e:
					time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: Odin [Status] decode Packet error, recording NaNs. Error: ' + e
				else:
					# We extract the status and voltage from the packet, Stack = (index, INP, INM, volt)
					head = self.sleipnir.extract_value(packet)
					if not	head[3] == 666 :
						head[3] = DT670.DT670(head[3])
					# We prepare the stack to be written to file
					body = ['adc'+str(head[0])+'_ch'+str(head[1])+'_'+str(head[2]),float(head[3])]
					# We put the receive time into the que to be writen to the time file
					self.io.que.put(['time', RXtime])
					# We write the voltage to the approriate file que
					self.io.que.put(body) 	 
			time.sleep(1)
		print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: Odin [Status]: Data aquisition thread has stopped!'
		
	def start(self):
		try:
			self.io.start()
			self.instio.start()
		except Exception, e:
			print e
			return 'DAQ did not start: could not find Sleipnir!'
		else:
			try:
				thread = threading.Thread(target=self.acquire_data, args=())
				thread.start()
			except Exception, e:
				print e
				return 'DAQ did not start!'
			else:
				return 'DAQ has started!'
			
		
	def stop(self):
		self.shutdown.set()
		while self.io.thread.isAlive() or self.instio.thread.isAlive() :
			time.sleep(1)
			
		self.shutdown.clear()
		print  time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: Odin [Status]: Data Aquisition has stopped and ready for more!'
		return 'DAQ has ended!'
	
	def version(self):
		return "tmp Version till git"
def main():
	print 'Odin, he who rides sleipnir, Has awoken!'
	hostname = socket.gethostname()
	
	if hostname == 'misterq':
		print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: Odin [Status]: The host has identified himself as MisterQ!'
		odin = Odin('/mnt/uranus/misterq/rawdata/diodes', '/mnt/uranus/misterq/conf.txt', '/mnt/uranus/misterq/current/diode', '/dev/ttyUSB1', 1250000)
		Pyro4.config.HOST = "192.168.0.66"
		Pyro4.Daemon.serveSimple(
				{
					odin: "MisterQ.Sleipnir"
				},
				ns = True)
	if hostname == 'missw':
		print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: Odin [Status]: The host has identified herself as MissW!'
		odin = Odin('/mnt/uranus/missw/rawdata/diodes', '/mnt/uranus/missw/conf.txt', '/mnt/uranus/missw/current/diode', '/dev/ttyUSB1', 1250000)
		Pyro4.config.HOST = "192.168.0.68"
		Pyro4.Daemon.serveSimple(
				{
					odin: "MissW.Sleipnir"
				},
				ns = True)
	else:
		print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: Odin [Status]: The host is not identified!'

if __name__=="__main__":
	main()
