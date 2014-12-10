# Dominik Gothe
# Parent Project: Sleipnir
# 12/09/2014
# Python 2.7

# Based on the Pedro Antonio Fluxa Rojas principle of finding dirfiles

# Relies on external:
  # matplotlib
  # numpy

from os import walk
from os import path

from time import strptime
from time import ctime
from time import mktime
from time import sleep

from numpy import fromfile
from numpy import average
from numpy import empty
from numpy import append

import struct
import itertools
import matplotlib.pyplot as plt

# mypath should point to the folder containing the time stamped diode dirfiles
mypath = '/mnt/niflheim/misterq/rawdata/diodes'
# time_form defines the time format with wich the dirfiles are stamped
time_form = "%Y-%m-%d-%H-%M-%S"

# let us grab all the folder names and store them in mydrinames
mydirnames = []
for ( dirpath, dirnames, filenames ) in walk( mypath ):
  mydirnames = dirnames
  break

# let us now create a dictionary translating the date stamp to ctime
mydict = {}
for folder in mydirnames:
  try:
    ctime = mktime( strptime( folder, time_form ) )
    mydict[ ctime ] = folder
  except ValueError:
    pass

# lets define the start and stop time using the given format
# this should be done via command line input
time_start = '2014-06-26-11-00-00'
time_stop  = '2014-06-27-18-40-00'
time_start_c = mktime( strptime( time_start, time_form ) )
time_stop_c  = mktime( strptime( time_stop , time_form ) )

# now let us create a list of the folders that we want to include
myfolders = []
for element in mydict:
  if time_start_c < element and element < time_stop_c:
    myfolders.append( mydict[ element ] )

myfolders.sort() # lets just make sure they are sorted by date

# add the channel's that you want to plot
sleipnir = {
  'adc2_ch1_COM':'diode 1 location',
  'adc2_ch2_COM':'diode 2 location',
  'adc2_ch3_COM':'diode 3 location',
  }

#
#
# This function will look in the supplied dirfile and return the average value of the fields in sleipnir
def avg_dirfile( dirfile_name ):
  try:
    time_file = open( path.join( mypath, dirfile_name, 'time' ) ) # try to open the time field
  except:
    print 'time file not found in',
    print dirfile_name
    print 'please cleanup the corrupt dirfile'
    raise # if we can't open the time field we have to quit
  else:
    time_arr = fromfile( time_file )
    time_val = average( time_arr ) # if all is good we use the average time value

  output = [ time_val ]

  for channel in sleipnir:
    try:
      tmp_file = open( path.join( mypath, dirfile_name, channel ) ) # try to open the channel field
    except:
      tmp_val = float('nan') # if it is not there we record a NaN value
    else:
      tmp_arr = fromfile( tmp_file )
      tmp_val = average( tmp_arr )
      output.append( tmp_val ) # if the field exists we record its average

  print 'done with',
  print dirfile_name
  return output # [ time, field0, field1, field2 ]

nfields = len( sleipnir ) + 1  # Number of fields, one for each channel + time
data = empty( [0, nfields] )  # setup an empty array to append to later

for folder in myfolders:
  data_list = avg_dirfile( folder ) # grab average dirfile
  data = append( data, [data_list], axis = 0 ) # append average values to our data matrix

print data.shape # lets just make sure it is what we expect

time = data[:,0] # extract the time vector from our data matrix

colors = itertools.cycle(['b', 'g', 'r', 'c', 'm','y']) # colors are pretty

# Lets plot some serious business
plt.figure(1)
plt.title( 'title' )
for channel in sleipnir:
  n = sleipnir.keys().index( channel ) # this is weird, but the index of the key maps to the index of the data matrix
  plt.plot( time, data[:, n+1 ], ',', color = next( colors ), label = sleipnir[ channel ] )
  plt.legend() # lets put a label on the legend
plt.show() 
