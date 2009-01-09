#!/usr/bin/env python
# encoding: utf-8
"""
xsil2graphicsParser.py

Created by Joe Hope on 2009-01-06.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.

"""
import os
import sys
import getopt
import xpdeint.Python24Support
import xml
from xml.dom import minidom
import xpdeint.minidom_extras

from xml.dom import minidom
import xpdeint.minidom_extras

from xpdeint.XSILFile import XSILFile

import numpy
import imp

from xpdeint.xsil2graphics2.MathematicaImport import MathematicaImport
from xpdeint.xsil2graphics2.RImport import RImport
from xpdeint.xsil2graphics2.MathematicaFiveImport import MathematicaFiveImport
from xpdeint.xsil2graphics2.GnuplotImport import GnuplotImport
from xpdeint.xsil2graphics2.MatlabImport import MatlabImport
from xpdeint.xsil2graphics2.ScilabImport import ScilabImport

# Hack for Leopard so it doesn't import the web rendering
# framework WebKit when Cheetah tries to import the Python
# web application framework WebKit
if sys.platform == 'darwin':
  module = type(sys)
  sys.modules['WebKit'] = module('WebKit')

# This is where we'll diverge when this isn't xpdeint any more.

# Import the parser stuff
from xpdeint.ParserException import ParserException, parserWarning


# The help message printed when --help is used as an argument
help_message = '''
usage: xsil2graphics2 [options] fileToBeParsed

Options and arguments for xpdeint:
-h          : Print this message (also --help)
-o filename : This overrides the name of the output file to be generated (also --output)
-d          : Debug mode (also --debug)
-n          : Only generate a source file, don't compile (also --no-compile)

Options:  (none of which are actually implemented)
  infile(s):        required, the input xsil file or files
  -h/--help:        optional, display this information
  -m/--matlab:      optional, produce matlab/octave output (default)
  -s/--scilab:      optional, produce scilab output
  -a/--mathmFive:   optional, produce mathematica 5.x output
  -e/--mathematica: optional, produce mathematica output
  -g/--gnuplot:     optional, produce gnuplot output
  -r/--R:           optional, produce R output
  -p/--plot:        optional, generate plotting output (matlab/octave)
  -o/--outfile:     optional, alternate output file name (one input file only)

For further help, please see http://www.xmds.org
'''

def anyObject(iterable):
  """
  Return an object from an iterable. This is designed to be used with sets
  because I can't work out any other way of doing this, but it will work
  with any iterable.
  """
  for obj in iterable:
    return obj


class Usage(Exception):
  """
  Exception class used when an error occurs parsing command
  line arguments.
  """
  def __init__(self, msg):
    self.msg = msg
  

def main(argv=None):
  # Default to not being verbose with error messages
  # If debug is true, then when an error occurs during parsing,
  # the Python backtrace will be shown in addition to the XML location
  # where the error occurred.
  debug = False
  
  plotFlag = False
  outputFormat = 'matlab'
  
  # Import version information
  from Preferences import versionString
  from Version import subversionRevisionString
  
  xpdeintUserDataPath = os.path.join(os.path.expanduser('~'), '.xmds')
  
  print "xsil2graphics2 from xpdeint version %(versionString)s (%(subversionRevisionString)s)" % locals()
  
  # Attempt to parse command line arguments
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.gnu_getopt(argv[1:], "hmsaegrpo:", ["help", "matlab", "scilab", "mathmFive", "mathematica", "gnuplot", "R", "plot", "outfile="])
    except getopt.error, msg:
      raise Usage(msg)
    
    output=''
    # option processing
    for option, value in opts:
      if option in ("-h", "--help"):
        raise Usage(help_message)
      if option in ("-o", "--outfile"):
        output = value
      if option in ("-p", "--plot"):
        plotFlag = True
      if option in ("-m", "--matlab"):
        outputFormat = 'matlab'
      if option in ("-s", "--scilab"):
        outputFormat = 'scilab'
      if option in ("-a", "--mathmFive"):
        outputFormat = 'mathmFive'
      if option in ("-e", "--mathematica"):
        outputFormat = 'mathematica'
      if option in ("-g", "--gnuplot"):
        outputFormat = 'gnuplot'
      if option in ("-r", "--R"):
        outputFormat = 'R'
        
    # argument processing
    if len(args)==1:
        xsilInputName = args[0]
    else:
        raise Usage(help_message)
  
  except Usage, err:
    print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
    print >> sys.stderr, "\t for help use --help"
    return 2
    
  try:
    inputXSILFile = XSILFile(xsilInputName, loadASCIIOnly=True)
  except Exception, err:
    print >> sys.stderr, "Exception raised while trying to read xsil file:", err
    return
    
# print dir(inputXSILFile)
  
  if outputFormat == 'R':
    templateClass = RImport
    if output=='':
      output=xsilInputName[0:-5]+'.R'
  
  if outputFormat == 'gnuplot':
    templateClass = GnuplotImport
    if output=='':
      output=xsilInputName[0:-5]+'.gnu'
  
  if outputFormat == 'matlab':
    templateClass = MatlabImport
    if output=='':
      output=xsilInputName[0:-5]+'.m'
  
  if outputFormat == 'mathmFive':
    templateClass = MathematicaFiveImport
    if output=='':
      output=xsilInputName[0:-5]+'.nb'

  if outputFormat == 'scilab':
    templateClass = ScilabImport
    if output=='':
      output=xsilInputName[0:-5]+'.sci'
    
  if outputFormat == 'mathematica':
    templateClass = MathematicaImport
    if output=='':
      output=xsilInputName[0:-5]+'.nb'
  
  outputTemplate = templateClass()
  
  # Now actually write the simulation to disk.
  
  outputFile = file(output, "w")
  print >> outputFile, outputTemplate.loadXSILFile(inputXSILFile)  
  print outputTemplate.loadXSILFile(inputXSILFile)  
  outputFile.close()

if __name__ == "__main__":
  sys.exit(main())
