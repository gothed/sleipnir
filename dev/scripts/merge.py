# Dominik Gothe
# Parent Project: Sleipnir
# 12/09/2014
# Python 2.7

# Relies on external matplotlib

from os import walk

from time import strptime
from time import ctime
from time import mktime
from time import sleep
import struct
from numpy import fromfile
from numpy import average
from os import path

from numpy import empty
from numpy import append

import itertools

import matplotlib.pyplot as plt

# Path should point to the folder containing the time stamped diode dirfiles
mypath = '/mnt/niflheim/misterq/rawdata/diodes'

time_form = "%Y-%m-%d-%H-%M-%S"


mydirnames = []

for ( dirpath, dirnames, filenames ) in walk( mypath ):
  mydirnames = dirnames
  break

mydict = {}
for folder in mydirnames:
  try:
    ctime = mktime( strptime( folder, time_form ) )
    mydict[ ctime ] = folder
  except ValueError:
    pass


time_start = '2014-06-26-11-00-00'
time_stop  = '2014-06-27-18-40-00'
time_start_c = mktime( strptime( time_start, time_form ) )
time_stop_c  = mktime( strptime( time_stop , time_form ) )

myfolders = []

for element in mydict:
  if time_start_c < element and element < time_stop_c:
    myfolders.append( mydict[ element ] )

myfolders.sort()

#print myfolders

# add the channel's that you want to plot
sleipnir = {
  'adc2_ch1_COM':'diode 1 location',
  'adc2_ch2_COM':'diode 2 location',
  'adc2_ch3_COM':'diode 3 location',
  }

def avg_dirfile( dirfile_name ):

  try:
    time_file = open( path.join( mypath, dirfile_name, 'time' ) )
  except:
    print 'time file not found in',
    print dirfile_name
    print 'please cleanup the corrupt dirfile'
    raise
  else:
    time_arr = fromfile( time_file )
    time_val = average( time_arr )

  output = [ time_val ]


  for channel in sleipnir:
    try:
      tmp_file = open( path.join( mypath, dirfile_name, channel ) )
    except:
      tmp_val = 999
    else:
      tmp_arr = fromfile( tmp_file )
      tmp_val = average( tmp_arr )
      output.append( tmp_val )

  print 'done with',
  print dirfile_name
  return output

nfields = len( sleipnir ) + 1  # Number of fields, one for each channel + time
data = empty( [0, nfields] )  # Setup the bases

for folder in myfolders:
  data_list = avg_dirfile( folder )
  data = append( data, [data_list], axis = 0 )

print data.shape

time = data[:,0]

colors = itertools.cycle(['b', 'g', 'r', 'c', 'm','y'])
locations = [
  'Diode Location 1',
  'Diode Location 2',
  'Diode Location 3',
]

plt.figure(1)
plt.title( 'title' )
for channel in sleipnir:
  n = sleipnir.keys().index( channel )
  plt.plot( time, data[:, n+1 ], ',', color = next( colors ), label = sleipnir[ channel ] )
  plt.legend()
plt.show()
