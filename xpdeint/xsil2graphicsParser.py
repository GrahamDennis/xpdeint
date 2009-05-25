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

from xpdeint.XSILFile import XSILFile

# Hack for Leopard so it doesn't import the web rendering
# framework WebKit when Cheetah tries to import the Python
# web application framework WebKit
if sys.platform == 'darwin':
  module = type(sys)
  sys.modules['WebKit'] = module('WebKit')

from xpdeint.xsil2graphics2.MathematicaImport import MathematicaImport
from xpdeint.xsil2graphics2.RImport import RImport
from xpdeint.xsil2graphics2.MathematicaFiveImport import MathematicaFiveImport
from xpdeint.xsil2graphics2.GnuplotImport import GnuplotImport
from xpdeint.xsil2graphics2.MatlabImport import MatlabImport
from xpdeint.xsil2graphics2.ScilabImport import ScilabImport


# The help message printed when --help is used as an argument
help_message = '''
usage: xsil2graphics2 [options] filenames [...]

Options and arguments for xpdeint:
-h          : Print this message (also --help)
-o filename : This overrides the name of the output file to be generated (also --output)
-d          : Debug mode (also --debug)

Options:  (Only Mathematica has been implemented)
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
  --debug:          Debug mode
  

For further help, please see http://www.xmds.org
'''

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
  
  # Import version information
  from Preferences import versionString
  from Version import subversionRevisionString
  
  print "xsil2graphics2 from xpdeint version %(versionString)s (%(subversionRevisionString)s)" % locals()
  
  # Attempt to parse command line arguments
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.gnu_getopt(argv[1:], "hmsaegrpo:", ["help", "matlab", "scilab", "mathmFive", "mathematica", "gnuplot", "R", "plot", "outfile=", "debug"])
    except getopt.error, msg:
      raise Usage(msg)
    
    plotFlag = False
    userSpecifiedFilename = None
    defaultExtension = None
    outputTemplateClass = MatlabImport
    
    optionList = [
      ("-m", "--matlab", MatlabImport),
      ("-s", "--scilab", ScilabImport),
      ("-a", "--mathmFive", MathematicaFiveImport),
      ("-e", "--mathematica", MathematicaImport),
      ("-g", "--gnuplot", GnuplotImport),
      ("-r", "--R", RImport),
    ]
    
    # option processing
    for option, value in opts:
      if option in ("-h", "--help"):
        raise Usage(help_message)
      if option in ("-o", "--outfile"):
        userSpecifiedFilename = value
      if option in ("-p", "--plot"):
        plotFlag = True
      if option == '--debug':
        debug = True
      for shortOpt, longOpt, importClass in optionList:
        if option in (shortOpt, longOpt):
          outputTemplateClass = importClass 
    
    if userSpecifiedFilename and len(args) > 1:
      print >> sys.stderr, "The '-o' option cannot be used when processing multiple xsil files."
    if not args:
      # No xsil files to process
      raise Usage(help_message)
  
  except Usage, err:
    print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
    print >> sys.stderr, "\t for help use --help"
    return 2
    
  outputTemplate = outputTemplateClass()
  print "Generating output for %s." % outputTemplate.name
  
  
  for xsilInputName in args:
    # If an output name wasn't specified, construct a default
    if not userSpecifiedFilename:
      # Strip off the '.xsil' extension
      baseName = os.path.splitext(xsilInputName)[0]
      # Grab the default extension from the output template
      outputFilename = baseName + '.' + outputTemplateClass.defaultExtension
    else:
      outputFilename = userSpecifiedFilename
    
    print "Writing import script for '%(xsilInputName)s' to '%(outputFilename)s'." % locals()
    
    try:
      inputXSILFile = XSILFile(xsilInputName, loadData='ascii')
    except IOError, err:
      print >> sys.stderr, "Exception raised while trying to read xsil file:", err
      if debug:
        raise
      return
    
    # Now actually write the simulation to disk.
    
    outputFile = file(outputFilename, "w")
    print >> outputFile, outputTemplate.loadXSILFile(inputXSILFile)  
    outputFile.close()
  

if __name__ == "__main__":
  sys.exit(main())
