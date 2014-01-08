#!/usr/bin/env python
# encoding: utf-8
"""
xsil2graphicsParser.py

Created by Joe Hope on 2009-01-06.
Modified by Thomas Antioch on 2013-07-18.

Copyright (c) 2009-2012, Joe Hope

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
import os
import sys
import getopt

from xpdeint.XSILFile import XSILFile
from xpdeint.IndentFilter import IndentFilter

# Hack for Mac OS X so it doesn't import the web rendering
# framework WebKit when Cheetah tries to import the Python
# web application framework WebKit
if sys.platform == 'darwin':
  module = type(sys)
  sys.modules['WebKit'] = module('WebKit')

from xpdeint.xsil2graphics2.MathematicaImport import MathematicaImport
from xpdeint.xsil2graphics2.MatlabOctaveImport import MatlabOctaveImport
from xpdeint.xsil2graphics2.PythonImport import PythonImport
from xpdeint.xsil2graphics2.RImport import RImport


# The help message printed when --help is used as an argument
help_message = '''
usage: xsil2graphics2 [options] filenames [...]

Options and arguments for xsil2graphics2:
-h          : Print this message (also --help)
-o filename : This overrides the name of the output file to be generated (also --output)
-d          : Debug mode (also --debug)

Options:
  infile(s):        required, the input xsil file or files
  -h/--help:        optional, display this information
  -m/--matlab:      optional, produce matlab output (default, also supports Octave)
  -e/--mathematica: optional, produce mathematica output
  -8/--octave:      optional, produce octave output (identical to MATLAB output)
  -p/--python:      optional, produce Python/pylab/matplotlib script (HDF5 requires h5py)
  -r/--R:           optional, produce R output
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
  
  print "xsil2graphics2 from xmds2 version %(versionString)s (%(subversionRevisionString)s)" % locals()
  
  # Attempt to parse command line arguments
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.gnu_getopt(argv[1:], "hm8epro:", ["help", "matlab", "octave", "mathematica", "python", "R", "outfile=", "debug"])
    except getopt.error, msg:
      raise Usage(msg)
    
    userSpecifiedFilename = None
    defaultExtension = None
    outputTemplateClass = MatlabOctaveImport
    
    optionList = [
      ("-m", "--matlab", MatlabOctaveImport),
      ("-8", "--octave", MatlabOctaveImport),
      ("-e", "--mathematica", MathematicaImport),
      ("-p", "--python", PythonImport),
      ("-r", "--R", RImport),
    ]
    
    # option processing
    for option, value in opts:
      if option in ("-h", "--help"):
        raise Usage(help_message)
      if option in ("-o", "--outfile"):
        userSpecifiedFilename = value
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
    
  outputTemplate = outputTemplateClass(filter=IndentFilter)
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
    try:
      file(outputFilename, 'w').write(outputTemplate.loadXSILFile(inputXSILFile))
    except Exception, err:
      print >> sys.stderr, 'ERROR:', err
    
  

if __name__ == "__main__":
  sys.exit(main())
