#!/usr/bin/env python
# encoding: utf-8
"""
parser2.py

Created by Graham Dennis on 2008-01-03.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""
import os
import sys
import getopt
import xpdeint.Python24Support
import xml
from xml.dom import minidom
import xpdeint.minidom_extras
import subprocess
from pkg_resources import resource_filename
import hashlib
import shutil

import cPickle

from xpdeint.Utilities import leopardWebKitHack

leopardWebKitHack()

from xpdeint.Preferences import xpdeintUserDataPath

# Import the parser stuff
from xpdeint.ParserException import ParserException, parserWarning
from xpdeint.XMDS2Parser import XMDS2Parser

# Import the top level template
from xpdeint.Simulation import Simulation as SimulationTemplate

# Import the IndentFilter. The IndentFilter is the magic filter
# that when used correctly makes the generated source correctly
# indented. See the comments in IndentFilter.py for more info.
from xpdeint.IndentFilter import IndentFilter

# Import the root class for all templates
from xpdeint._ScriptElement import _ScriptElement

# Import the Configuration module
from xpdeint import Configuration

# The help message printed when --help is used as an argument
help_message = '''
usage: xmds2 [options] fileToBeParsed

Options and arguments:
-h                              : Print this message (also --help)
-o filename                     : This overrides the name of the output file to be generated (also --output)
-d                              : Debug mode (also --debug)
-n                              : Only generate a source file, don't compile (also --no-compile)
--configure                     : Run configuration checks for compiling simulations
--reconfigure                   : Run configuration using the same options as used with the last
                                  time --configure was run with the additional arguments specified
--include-path /path/to/include : Add the path /path/to/include to the list of paths searched for include headers
                                  This option is only meaningful when used with --(re)configure
--lib-path /path/to/lib         : Add the path /path/to/lib to the list of paths searched for libraries
                                  This option is only meaningful when used with --(re)configure
'''

def fileContentsHash(filename):
  return hashlib.sha1(file(filename).read()).hexdigest()
  

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
  
  compileScript = True
  noVersionInformation = False
  
  # Import version information
  from Preferences import versionString
  from Version import subversionRevisionString
  
  print "xmds2 version %(versionString)s (%(subversionRevisionString)s)" % locals()
  
  if not os.path.isdir(xpdeintUserDataPath):
      os.mkdir(xpdeintUserDataPath)
  
  # Attempt to parse command line arguments
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.gnu_getopt(
                    argv[1:],
                    "ghno:",
                    [
                      "debug",
                      "help",
                      "no-compile",
                      "output=",
                      "no-version",
                      "configure",
                      "reconfigure",
                      "include-path=",
                      "lib-path=",
                    ]
      )
    except getopt.error, msg:
      raise Usage(msg)
    
    includePaths = []
    libPaths = []
    run_config = False
    run_reconfig = False
    
    sourceFilename = None
    # option processing
    for option, value in opts:
      if option in ("-g", "--debug"):
        debug = True
      elif option in ("-h", "--help"):
        raise Usage(help_message)
      elif option in ("-o", "--output"):
        sourceFilename = value
      elif option in ("-n", "--no-compile"):
        compileScript = False
      elif option == "--no-version":
        # This option is here for the test suite so that the generated source files don't
        # contain version information. This makes it easier to check if the source for a script
        # has changed as otherwise it would change every time the subversison revision number
        # increased
        noVersionInformation = True
      elif option == "--configure":
        run_config = True
      elif option == '--reconfigure':
        run_reconfig = True
      elif option == '--include-path':
        includePaths.append(value)
      elif option == '--lib-path':
        libPaths.append(value)
    
    if run_config:
      return Configuration.run_config(includePaths, libPaths)
    elif run_reconfig:
      return Configuration.run_reconfig(includePaths, libPaths)
    
    # argument processing
    if len(args) == 1:
        scriptName = args[0]
    else:
        raise Usage(help_message)
  
  except Usage, err:
    print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
    print >> sys.stderr, "\t for help use --help"
    return 2
  
  if not os.path.isfile(os.path.join(xpdeintUserDataPath, 'wscript')) or \
    fileContentsHash(os.path.join(xpdeintUserDataPath, 'wscript')) \
       != fileContentsHash(resource_filename(__name__, 'support/wscript')):
    print "Reconfiguring xpdeint (updated config script)..."
    wscript_path = resource_filename(__name__, 'support/wscript')
    dest_wscript_path = os.path.join(xpdeintUserDataPath, 'wscript')
    shutil.copyfile(wscript_path, dest_wscript_path)
    
    Configuration.run_reconfig()
  
  # globalNameSpace is a dictionary of variables that are available in all
  # templates
  globalNameSpace = {'scriptName': scriptName, 'simulationName': os.path.splitext(scriptName)[0]}
  
  if noVersionInformation:
    versionString = "VERSION_PLACEHOLDER"
    subversionRevisionString = "SUBVERSION_REVISION_PLACEHOLDER"
  
  # Open the script file
  try:
    scriptFile = file(scriptName)
  except Exception, err:
    print >> sys.stderr, "Exception raised while trying to read xmds script:", err
    return -1
  
  # Read the contents of the file
  globalNameSpace['inputScript'] = scriptFile.read().expandtabs()
  # Close the file
  scriptFile.close()
  del scriptFile
  
  # Parse the XML input script into a set of XML
  # classes
  try:
    xmlDocument = minidom.parseString(globalNameSpace['inputScript'])
  except xml.parsers.expat.ExpatError, err:
    print >> sys.stderr, "XML Parser error:", err
    return -1
  except Exception, err:
    print >> sys.stderr, "Exception raised during parsing xmds script:", err
    return -1
  
  # Attempt to import lxml and run the script through
  # the schema
  try:
    from lxml import etree
  except ImportError, err:
    pass
  else:
    # Parse the schema
    relaxng_doc = etree.parse(resource_filename(__name__, 'support/xpdeint.rng'))
    relaxng = etree.RelaxNG(relaxng_doc)
    # Parse the script
    script_doc = etree.fromstring(globalNameSpace['inputScript'])
    if not relaxng.validate(script_doc):
      # Validation failed
      for error in relaxng.error_log:
        parserWarning((error.line, error.column), error.message)
  
  
  globalNameSpace['debug'] = debug
  globalNameSpace['xmlDocument'] = xmlDocument
  globalNameSpace['features'] = {}
  globalNameSpace['fields'] = []
  globalNameSpace['simulationVectors'] = []
  globalNameSpace['momentGroups'] = []
  globalNameSpace['symbolNames'] = set()
  globalNameSpace['xmds'] = {'versionString': versionString,
                             'subversionRevision': subversionRevisionString}
  globalNameSpace['templates'] = set()
  globalNameSpace['precision'] = 'double'
  globalNameSpace['simulationBuildVariant'] = set()
  globalNameSpace['simulationUselib'] = set()
  globalNameSpace['bugReportAddress'] = 'xmds-devel@lists.sourceforge.net'
  
  xpdeintDataCachePath = os.path.join(xpdeintUserDataPath, 'xpdeint_cache')
  dataCache = {}
  if os.path.isfile(xpdeintDataCachePath):
    try:
      dataCacheFile = open(xpdeintDataCachePath, 'rb')
      dataCache = cPickle.load(dataCacheFile)
      dataCacheFile.close()
      del dataCacheFile
    except Exception, err:
      print >> sys.stderr, "Warning: Unable to load xpdeint data cache."
      if debug: raise
  globalNameSpace['dataCache'] = dataCache
  
  # We need the anyObject function in a few templates, so
  # we add it to the globalNameSpace, so that the function can
  # be called from a template like $anyObject(someContainer)
  globalNameSpace['anyObject'] = anyObject
  
  # Now start the process of parsing the XML class structure
  # onto a template heirarchy.
  try:
    parser = None
    
    # Check if the XML claims to be an XMDS2 script
    if XMDS2Parser.canParseXMLDocument(xmlDocument):
      parser = XMDS2Parser()
    
    # We don't have a parser that understands the XML, so we must bail
    if not parser:
      print >> sys.stderr, "Unable to recognise file as an xmds script."
      return -1
    
    # Set our magic filter
    filterClass = IndentFilter
    # Construct the top-level template class
    simulationTemplate = SimulationTemplate(parent = None, searchList=[globalNameSpace], filter=filterClass)
    _ScriptElement.simulation = simulationTemplate
    # Now get the parser to do the complex job of mapping the XML classes onto our
    # templates.
    parser.parseXMLDocument(xmlDocument, globalNameSpace, filterClass)
    
    # Now run preflight stage
    # Preflight is the stage which maps vector names, etc to the actual vectors themselves. It also
    # allows all templates to check that all of their settings are sane, and raise an exception if
    # there is a problem.
    #
    
    # Loop over a copy because we may create templates during iteration
    for template in _ScriptElement.simulation.children[:]:
      if not template._haveBeenRemoved:
        template.implementationsForFunctionName('bindNamedVectors')
    
    for template in _ScriptElement.simulation.children[:]:
      if not template._haveBeenRemoved:
        template.implementationsForFunctionName('preflight')
    
    # Preflight is done
    # We don't need the 'simulationVectors' variable any more.
    del globalNameSpace['simulationVectors']
    
    # Now build the map of transforms needed in the simulation
    globalNameSpace['features']['TransformMultiplexer'].buildTransformMap()
    
    
    # Final conversion to string
    simulationContents = str(simulationTemplate)
    
  # If there was an exception during parsing or preflight, a ParserException should have been
  # raised. The ParserException knows the XML element that triggered the exception, and the 
  # error string that should be presented to the user.
  except ParserException, err:  
    # Print the error to the user
    lineNumber = err.lineNumber
    columnNumber = err.columnNumber
    print >> sys.stderr, err.msg
    if not lineNumber == None:
      positionReference =  ["    Error caused at line %(lineNumber)i" % locals()]
      if not columnNumber == None:
        positionReference.append(", column %(columnNumber)i" % locals())
      positionReference.append(":\n")
      positionReference.append(globalNameSpace['inputScript'].splitlines(True)[lineNumber-1])
      if not columnNumber == None:
          positionReference.append(" "*(columnNumber-1) + "^~~ here.")
      print >> sys.stderr, ''.join(positionReference)
    if debug:
      if err.element:
        print >> sys.stderr, "    In element: " + err.element.userUnderstandableXPath()
      else:
        print >> sys.stderr, "    Unknown element. Please report this error to %s" % globalNameSpace['bugReportAddress']
    
    # If we have the debug option on, then in addition to the path to the XML element
    # that triggered the exception, print a traceback showing the list of Python function
    # calls that led to the exception being hit.
    if debug:
      raise
    
    return -1
  
  dataCache = globalNameSpace['dataCache']
  if dataCache:
    try:
      dataCacheFile = file(xpdeintDataCachePath, 'w')
    except IOError, err:
      print >> sys.stderr, "Warning: Unable to write xpdeint data cache. " \
                           "Ensure '%(xpdeintUserDataPath)s' exists and is writable." % locals()
    else:
      cPickle.dump(dataCache, dataCacheFile, protocol = 2)
      dataCacheFile.close()
  
  
  # Now actually write the simulation to disk.
  
  if not sourceFilename:
    sourceFilename = globalNameSpace['simulationName']
  
  if not sourceFilename.endswith('.cc'):
    sourceFilename += '.cc'
  
  if not debug:
    lines = simulationContents.splitlines(True)
    for lineNumber, line in enumerate(lines[:]):
      if '_XPDEINT_CORRECT_MISSING_LINE_NUMBER_' in line:
        lines[lineNumber] = line.replace('_XPDEINT_CORRECT_MISSING_LINE_NUMBER_', '%i "%s"' % (lineNumber+2, sourceFilename))
    simulationContents = ''.join(lines)
  
  file(sourceFilename, 'w').write(simulationContents)
  
  if debug:
    globalNameSpace['simulationUselib'].add('debug')
    globalNameSpace['simulationUselib'].discard('vectorise')
  
  if not globalNameSpace['simulationUselib'].intersection(['debug']):
    globalNameSpace['simulationUselib'].add('optimise')
  
  buildKWs = {
    'includes': resource_filename(__name__, 'includes'),
    'uselib': list(globalNameSpace['simulationUselib']),
  }
  
  if 'CFlags' in globalNameSpace['features']:
    buildKWs['CXXFLAGS'] = globalNameSpace['features']['CFlags'].cflags()
  
  variant = globalNameSpace['simulationBuildVariant']
  if not variant:
    variant.add('default')
  
  assert len(variant) == 1
  
  compilerLine = Configuration.run_build(
    sourceFilename,
    sourceFilename[:-3], # strip of trailing '.cc'
    variant = anyObject(variant),
    buildKWs = buildKWs
  )
  
  if not compilerLine:
      return -1
  
  if compileScript:
    print "\n",compilerLine,"\n"
    
    proc = subprocess.Popen(compilerLine, shell=True)
    return proc.wait()
  else:
    # Don't compile the script, but show how we would compile it
    print "\nWould compile with:\n",compilerLine,"\n"

if __name__ == "__main__":
  sys.exit(main())
