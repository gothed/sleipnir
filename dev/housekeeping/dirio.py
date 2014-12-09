# Dominik Gothe
# gothed [magic email symbol] pha.jhu.edu
# Parent Project: Beefy Miracle
# 07/30/2014
# Python 2.7

import json
import datetime
import os
import Queue
import threading
import time
import struct
import math

class dirio:
  conf = ""                     # json loaded configuration
  outfiles = {}                 # A dictionary of data files
  que = Queue.Queue()           # The que is daemonically monitored and written to disk
  creationtime = ""             # used to create new dirfile after a certain time
  logFile = ""                  # The log file will record any IO errors

  # 
  def __init__(self, shutdown, autostart=False, path='/mnt/alfheim/data_default', confFile='./default_setup.txt', sympath='/mnt/alfheim/data_default/current/diode', dirtime=60000):
    self.shutdown = shutdown    # shutdown signal
    self.path     = path        # top data directory
    self.confFile = confFile    # location of configuration file
    self.dirtime  = dirtime     # The time frame for datacolleciton into a single dirfile
    self.sympath  = sympath     # Symlink for most current data
    self.thread   = threading.Thread(target=self.writeque, args=())
    
    if autostart:
      self.start()

  def start(self):
    self.loadconfig()
    self.dirsetup()
    # Lets start a thread that will write the que to disk
    self.thread.start()
    
  # 
  # Reads a JASON formatted configuration file.
  # Returns a dict with the conf file information.
  def loadconfig(self):
    conf_tmp = ""
    for line in open(self.confFile).readlines():
        # anything starting with # will be skipped
        cleanLine = line[0:line.find("#")].strip() if "#" in line else line.strip()
        if cleanLine != "":
          conf_tmp += cleanLine.strip() 
    
    try:
      # now we have a dict of the configuration parameters
      self.conf = json.loads(conf_tmp)
    except Exception as e:
    
      print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + " ::: DirIO [Exception]: Failed to load configuration, please ensure you have valid json.\n", e
      exit()
  
  
  # Given a configuration, the dirfiles are opened.
  def dirsetup(self):
    self.creationtime = time.time()
    dirname = os.path.join(self.path, datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S'))

    try:
      os.makedirs(dirname)
    except OSError, e:
      if e.errno != 17:
        raise # This was not a "file exists" error.

    try:
      os.symlink(dirname, self.sympath)
    except OSError, e:
      if e.errno == 17:
        os.unlink(self.sympath)
        os.symlink(dirname, self.sympath)
        print 'Symlink already existet. Please shutdown sleipnir properly next time!'
      else:
        raise # This is not a "file exists" error.
         
    # now lets create all the file elemets
    
    samples = 0
    # Create a FORMAT file with sine, cosine, and time called out.
    fmt_file = open(os.path.join(dirname, 'format'), 'w')
    # print adc
    # for every adc lets create a new dict of channels
    for target in self.conf['dirfiles']:
      if not "dmy" in target and not "mux" in target:
        # for every ch of an adc lets open a file
        self.outfiles[target] = open(os.path.join(dirname, target), 'w')
        fmt_file.write(target+" RAW FLOAT64 1\n")
        samples+= 1
    if not 'mux' in self.conf['dirfiles']:
      samples=1
            
  
    self.outfiles['time'] = open(os.path.join(dirname, 'time'), 'w')
    fmt_file.write('time RAW FLOAT64 '+str(samples)+'\n')
    fmt_file.write('/REFERENCE time')
    fmt_file.close()
    # now all of your open files are indexed into outfiles, as a 2D array
    
  # Given a configuration, the dirfiels are closed.
  def dirclose(self):
    # Close all data streams
    for target in self.outfiles:
      self.outfiles[target].close()
    
    # Unlink the symlink: Note OS has to support this
    os.unlink(self.sympath)
    # Recreate the thread
    self.thread = threading.Thread(target=self.writeque, args=())
  
  # Write the data que to disk
  def writeque(self):
    print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + " ::: DirIO [Status]: Daemonically writing the que to disk"
    while not self.shutdown.is_set():
      while not self.que.empty():
        head = self.que.get()
        try:
          self.outfiles[head[0]].write(struct.pack('d', head[1]))
        except Exception, e:
          print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + " ::: DirIO [Exception]: " + e
      for i in self.outfiles:
        self.outfiles[i].flush()
      now = time.time()
      now = int(now) / self.dirtime * self.dirtime
      roundtime = int(self.creationtime) / self.dirtime * self.dirtime
      if now - roundtime >= self.dirtime:
        self.dirclose()
        self.dirsetup()
      else:
        time.sleep(1)
    
    self.dirclose()
    self.thread = threading.Thread(target=self.writeque, args=())
    print time.strftime('%H%m.%S %d:%m:%Y',time.gmtime()) + " ::: DirIO [Status]: Goodbye! Have a beautiful time!"
    
  # warning, this function can cause unrecoverable errors:
  def write_corruptdata(self):
    for files in self.outfiles:
      self.outfiles[files].write( struct.pack('d', float('nan')) )
      self.outfiles[files].flush()
      for i in range(23):
        # Raises and exception if que remains empty for 10 second
        self.que.get(True, 10)
