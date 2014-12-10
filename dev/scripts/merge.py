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

import sys
import socket
import struct
import itertools
import matplotlib.pyplot as plt

class Merger( object ):
  def __init__( self, mypath, time_format = '%Y-%m-%d-%H-%M-%S' ):
    self.path = mypath      # Path to the folder containing the time stamped dirfiles
    self.frmt = time_format # Format used to stamp dirfiles
    # define the sleipnir dictionary (refer to the man page)
    self.sleipnir = { 'channel0' : 'channel0 name' }

  # avg_dirfile returns the average value of the dirfile fields
  # the fields of interest are defined in sleipnir
  # the input is simply the folder name
  def avg_dirfile( self, dirfile_name ):
    # try to load the time file, if this doesn't exist we have to exist the program
    try:
      time_file = open( path.join( self.path, dirfile_name, 'time' ) )
    except:
      print 'time file not found in',
      print dirfile_name
      print 'please cleanup the corrupt dirfile'
      raise
    else:
      time_arr = fromfile( time_file )  # Create array from file
      time_val = average( time_arr )    # Average the array

    # Record the average time value in the first position of the output
    output = [ time_val ]

    # Now try to average all the fields in sleipnir
    for channel in self.sleipnir:
      try:
        tmp_file = open( path.join( self.path, dirfile_name, channel ) )
      except:
        tmp_val = float( 'nan' )        # Record a NaN value if the channel field is not found
      else:
        tmp_arr = fromfile( tmp_file )  # Create array from file
        tmp_val = average( tmp_arr )    # Average the array
        output.append( tmp_val )        # If the field exists append its average value to the output

    # Lets let the user know that we finished the dirfile
    print 'done with',
    print dirfile_name
    # Return the list of average values: [time, channel0, channel1, ...]
    return output
  
  #
  # find_dirfiles identifies all the folders between the given start:stop range
  # This is the Pedro Antonio Fluxa Rojas principle of finding dirfiles
  def find_dirfiles( self, start_time, stop_time ):
    self.start = start_time # Ignore anything before this time 
    self.stop  = stop_time  # Ignore anything after this time
    # translate the input into ctimes
    self.cstart = mktime( strptime( start_time, self.frmt ) )
    self.cstop  = mktime( strptime( stop_time , self.frmt ) )

    # let us grab all the folder names and store them in mydrinames
    mydirnames = []
    for ( dirpath, dirnames, filenames ) in walk( self.path ):
      mydirnames = dirnames
      break

    # let us now create a dictionary translating the date stamp to ctime
    mydict = {}
    for folder in mydirnames:
      try:
        ctime = mktime( strptime( folder, self.frmt ) )
        mydict[ ctime ] = folder
      except ValueError:
        pass

    # now let us create a list of the folders that we want to include
    myfolders = []
    for element in mydict:
      if self.cstart < element and element < self.cstop:
        myfolders.append( mydict[ element ] )

    myfolders.sort()  # lets just make sure they are sorted by date
    return myfolders  # now return the list of folders

  def plot( self, folders, processor ):
    nfields = len( self.sleipnir ) + 1              # Number of fields, one for each channel + time
    data = empty( [0, nfields] )                    # setup an empty array to append to later

    print data.shape

    for folder in folders:
      data_list = processor( folder )               # manipulate the dirfile according to the processor function
      data = append( data, [data_list], axis = 0 )  # append average values to our data matrix

    print data.shape                                # lets just make sure it is what we expect
    time = data[:,0]                                # extract the time vector from our data matrix
    color_list = ['b', 'g', 'r', 'c', 'm','y']      # colors are pretty
    colors = itertools.cycle( color_list )          # cycle through the color list

    # Lets plot some serious business
    plt.figure(1)
    plt.title( 'title' )
    for channel in self.sleipnir:
      n = self.sleipnir.keys().index( channel )     # this is weird, but the index of the key maps to the index of the data matrix
      plt.plot( time, data[:, n+1 ], 'o', color = next( colors ), label = self.sleipnir[ channel ] )
      plt.legend()                                  # lets put a label on the legend
    plt.show()

#
#
# MergerQ inherits from Merger but knows MisterQ's sleipnir configuration
class MergerQ( Merger ):
  def __init__( self, mypath, time_format = '%Y-%m-%d-%H-%M-%S' ):
    # Init the super class
    Merger.__init__( self, mypath, time_format )
    # Define sleipnir according to MisterQ's standards
    # comment anything you don't want to plot
    self.sleipnir =  {
      'adc2_ch3_COM':'60K Plate BF',
      'adc2_ch4_COM':'60K Plate DFT',
      'adc2_ch5_COM':'60K Plate HFT',
#      'adc2_ch6_COM':'60K Radiation 3/3',
      'adc2_ch7_COM':'60K Radiation 2/3',
#      'adc2_ch8_COM':'60K Radiation 1/3',
      'adc2_ch9_COM':'60K Radiation 0/3',
      'adc2_ch10_COM':'Free Floating',
      'adc2_ch11_COM':'Thermal Filter Stack',
      'adc1_ch0_COM':'Cal Plate',
      'adc1_ch1_COM':'Cal Plate',
      'adc1_ch2_COM':'SA Heat Sink',
      'adc1_ch3_COM':'BF Wire FT',
      'adc1_ch4_COM':'4K Radiation 3/3',
#      'adc1_ch5_COM':'4K Radiation 2/3',
      'adc1_ch6_COM':'4K Radiation 1/3',
#      'adc1_ch7_COM':'4K Radiation 0/3',
      'adc1_ch8_COM':'Free Float',
      'adc1_ch9_COM':'Thermal Filter Stack'      
    }


def main():
  print 'Let the merging commence.'
  # create the merger, Q, W, Wjr, HF
  # needs ( path, start_time, stop_time )
  # refer to man page for sys arg usage
  path        = sys.argv[1] # Data path
  start_time  = sys.argv[2] # start date
  stop_time   = sys.argv[3] # stop date

  hostname = socket.gethostname()

  if hostname == 'misterq':
    merger = MergerQ( path )
  else:
    print 'Host not known, will use MisterQ configuration.'
    merger = MergerQ( path )
  myfolders = merger.find_dirfiles( start_time, stop_time )
  # you can define a custom dirfile processor and pass this to the plot function instead
  merger.plot( myfolders, merger.avg_dirfile )

if __name__ == "__main__":
  main()
