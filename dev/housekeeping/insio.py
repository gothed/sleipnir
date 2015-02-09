# Dominik Gothe
# gothed [magic email symbol] pha.jhu.edu
# Parent Project: Beefy Miracle
# 07/30/2014
# Python 2.7

import struct
import serial
import time
import Queue
import threading

class MalformedPacket(Exception):
  pass

class insio:
  pktque = Queue.Queue()
  decoded_packet = ""
  # Exposes the USB com port, sperator flag and packet size.
  def __init__(self, shutdown, autostart, stream='/dev/ttyUSB1', baud=1250000, pktsize=7):
    self.shutdown = shutdown
    self.autostart = autostart
    
    #self.stream = serial.serial_for_url(url=stream, baudrate=baud, stopbits=2, rtscts=1, timeout = 2, do_not_open=True)
    self.stream  = serial.Serial(port=None, baudrate=baud, stopbits=2, rtscts=1, timeout = 2) # Connect to instrument VCP
    self.stream.port = stream
    self.pktsize = pktsize # STD size of COBS package
    self.thread = threading.Thread(target=self.findpkts,args=())
    
    if autostart:
      self.start()
      
  def start(self):
    self.stream.open()
    print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: InstIO [Status]: Daemonically finding Packets.'
    self.thread.start()
 
  def findpkts(self):
    while not self.shutdown.is_set():
      try:
        self.pktque.put(self.pktfind())
      except Exception, e:
        print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + ' ::: InstIO [Exception]: ' + str( e )
      
    self.stream.close()
    self.thread = threading.Thread(target=self.findpkts,args=())
    print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + " ::: InstIO [Status]: Goodbye! Have a beatuiful time!"
      
  # Look through the data stream untill a valid packet is found.
  def pktfind(self):
    buf = self.stream.read(self.pktsize)
    if len( buf ) != self.pktsize:
    	raise Exception('The read operation probably timed out!')
    	
    done = 0
    while not done :
      if 0x00 == struct.unpack_from(">B", buf[0])[0]:
        done = 1
        index = 0
        for i in range (1, self.pktsize):
          if 0x00 == struct.unpack_from(">B", buf[i])[0]:
            index = i
            done = 0
        if index > 0:
          print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + "Multiple Flags Found:"
          print ":".join("{0:x}".format(ord(c)) for c in buf)
          buf = buf[index:] + self.stream.read(index)
          assert len(buf) == self.pktsize
      else:
        print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + " ::: InstIO [Error]: Flag not found, advancing buffer by one. " + ":".join("{0:x}".format(ord(c)) for c in buf)
        buf = buf[1:] + self.stream.read(1)
    return (buf[1:self.pktsize],time.time())
  
  # Decode COBS packets.
  # COBS replaces all occurences of the FLAG byte with a byte indicating the location of the next flag.
  # The first byte locates the first FLAG byte.
  def decodeCOBS(self, packet):
    packet = list(packet) # KirkMcDonal says this line is not necessary
    # code indicates the location of the first code
    code = struct.unpack_from(">B", packet[0])[0]  # Convert the first string in the list to a byte
    
    # If the first code indicates a flag byte within the packet then work has to be done
    if code < self.pktsize:
      # So long as the code byte is not the last byte
      while code < ( self.pktsize - 1 ):
        new_code = struct.unpack_from(">B", packet[code])[0]
        if new_code == 0x00 or new_code > ( self.pktsize - 1 - code):
          raise MalformedPacket("COBS Decode Failed")
        packet[code] = '\x00'
        code += new_code
      # If the code byte is the last byte, replace it with the FLAG
      if code == ( self.pktsize - 2 ):
        packet[code] = '\x00'
    
    new_packet = "".join(packet[1:self.pktsize])

    return new_packet
  
  def decodePacket(self):
    (encoded_packet, now) = self.pktque.get()
    self.decoded_packet = self.decodeCOBS(encoded_packet)
    return (self.decoded_packet,now)
  
  def clearBuffers(self):
    self.stream.flushOutput()
    self.stream.flushInput()
    
    
  # When passed an instance of 'sleipnir', for example
  # this function will send the programming sequence as
  # defined by sleipnir.progmem!
  def reprogram(self, device):
    stream.write(device.progmem)
