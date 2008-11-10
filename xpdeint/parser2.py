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

import imp

# Hack for Leopard so it doesn't import the web rendering
# framework WebKit when Cheetah tries to import the Python
# web application framework WebKit
if sys.platform == 'darwin':
  module = type(sys)
  sys.modules['WebKit'] = module('WebKit')


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

# The help message printed when --help is used as an argument
help_message = '''
usage: xpdeint [options] fileToBeParsed

Options and arguments:
-h          : Print this message (also --help)
-o filename : This overrides the name of the output file to be generated (also --output)
-d          : Debug mode (also --debug)
-n          : Only generate a source file, don't compile (also --no-compile)
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
  
  compileScript = True
  noVersionInformation = False
  
  # Attempt to parse command line arguments
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.gnu_getopt(argv[1:], "dhno:", ["debug", "help", "no-compile", "output=", "no-version"])
    except getopt.error, msg:
      raise Usage(msg)
    
    output=''
    # option processing
    for option, value in opts:
      if option in ("-d", "--debug"):
        debug = True
      if option in ("-h", "--help"):
        raise Usage(help_message)
      if option in ("-o", "--output"):
        output = value
      if option in ("-n", "--no-compile"):
        compileScript = False
      if option == "--no-version":
        # This option is here for the test suite so that the generated source files don't
        # contain version information. This makes it easier to check if the source for a script
        # has changed as otherwise it would change every time the subversison revision number
        # increased
        noVersionInformation = True
    
    # argument processing
    if len(args)==1:
        scriptName = args[0]
    else:
        raise Usage(help_message)
  
  except Usage, err:
    print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
    print >> sys.stderr, "\t for help use --help"
    return 2
    
  # globalNameSpace is a dictionary of variables that are available in all
  # templates
  globalNameSpace = {'scriptName': scriptName}
  
  
  # Open the script file
  try:
    scriptFile = file(scriptName)
  except Exception, err:
    print >> sys.stderr, "Exception raised while trying to read xmds script:", err
    return
  
  # Read the contents of the file
  globalNameSpace['inputScript'] = scriptFile.read()
  # Close the file
  scriptFile.close()
  del scriptFile
  
  # Parse the XML input script into a set of XML
  # classes
  try:
    xmlDocument = minidom.parse(scriptName)
  except xml.parsers.expat.ExpatError, err:
    print >> sys.stderr, "XML Parser error:", err
    return
  except Exception, err:
    print >> sys.stderr, "Exception raised during parsing xmds script:", err
    return
  
  # Set up the globalNameSpace with the appropriate variables
  from Preferences import versionString
  from Version import subversionRevisionString
  
  if noVersionInformation:
    versionString = "VERSION_PLACEHOLDER"
    subversionRevisionString = "SUBVERSION_REVISION_PLACEHOLDER"
  
  globalNameSpace['debug'] = debug
  globalNameSpace['xmlDocument'] = xmlDocument
  globalNameSpace['features'] = {}
  globalNameSpace['fields'] = []
  globalNameSpace['vectors'] = []
  globalNameSpace['momentGroups'] = []
  globalNameSpace['symbolNames'] = set()
  globalNameSpace['xmds'] = {'versionString': versionString,
                             'subversionRevision': subversionRevisionString}
  globalNameSpace['templates'] = set()
  globalNameSpace['transforms'] = {}
  
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
      return
    
    # Set our magic filter
    filterClass = IndentFilter
    # Construct the top-level template class
    simulationTemplate = SimulationTemplate(parent = None, searchList=[globalNameSpace], filter=filterClass)
    _ScriptElement.simulation = simulationTemplate
    globalNameSpace['simulation'] = simulationTemplate
    # Now get the parser to do the complex job of mapping the XML classes onto our
    # templates.
    parser.parseXMLDocument(xmlDocument, globalNameSpace, filterClass)
    
    # Now run preflight stage
    # Preflight is the stage which maps vector names, etc to the actual vectors themselves. It also
    # allows all templates to check that all of their settings are sane, and raise an exception if
    # there is a problem.
    #
    
    # Loop over a copy because we may create templates during iteration
    for template in globalNameSpace['simulation'].children[:]:
      if not template._haveBeenRemoved:
        template.implementationsForFunctionName('bindNamedVectors')
    
    for template in globalNameSpace['simulation'].children[:]:
      if not template._haveBeenRemoved:
        template.implementationsForFunctionName('preflight')
    
    # Preflight is done
    
    # We don't need the 'vectors' variable any more.
    del globalNameSpace['vectors']
    
    # Now we need to do a dry-run conversion of the simulation template to a 
    # string. This is necessary so that various bits of information that will
    # only be known once the template is written will be available for modifying
    # the template. One example is creating a comprehensive set of fft plans
    # requires knowledge of which vector will be required in which space. As this
    # information is only found out as the template is converted to a string, we
    # must do this at least once before we actually write the template to file.
    
    simulationContents = str(simulationTemplate)
    del simulationContents
    # Clear the guards that will have been set up
    _ScriptElement.resetGuards()
    
    
  # If there was an exception during parsing or preflight, a ParserException should have been
  # raised. The ParserException knows the XML element that triggered the exception, and the 
  # error string that should be presented to the user.
  except ParserException, err:  
    # Print the error to the user
    lineNumber = err.lineNumber
    columnNumber = err.columnNumber
    # Indent multiline error messages
    if err.msg.count('\n'):
      msg = err.msg.splitlines()
      msg[1:] = [' '*len("ERROR: ") + line for line in msg[1:]]
      err.msg = '\n'.join(msg)
    print >> sys.stderr, "ERROR: " + err.msg
    if not lineNumber == None:
      positionReference =  "    At line %(lineNumber)i" % locals()
      if not columnNumber == None:
        positionReference += ", column %(columnNumber)i" % locals()
      positionReference += "."
      print >> sys.stderr, positionReference
    if debug:
      if err.element:
        print >> sys.stderr, "    In element: " + err.element.userUnderstandableXPath()
      else:
        print >> sys.stderr, "    Unknown element. Please report this error to xmds-devel@lists.sourceforge.net"
    
    # If we have the debug option on, then in addition to the path to the XML element
    # that triggered the exception, print a traceback showing the list of Python function
    # calls that led to the exception being hit.
    if debug:
      raise
    
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
      # print error, error.domain_name, error.type_name, error.message, dir(error)
  
  
  # Now actually write the simulation to disk.
  
  if output == '':
    output = globalNameSpace['simulationName']
  sourceFileName = output + '.cc'
  myfile = file(sourceFileName, "w")
  simulationContents = str(simulationTemplate)
  if not debug:
    lines = simulationContents.splitlines(True)
    for lineNumber, line in enumerate(lines[:]):
      if '_XPDEINT_CORRECT_MISSING_LINE_NUMBER_' in line:
        lines[lineNumber] = line.replace('_XPDEINT_CORRECT_MISSING_LINE_NUMBER_', '%i "%s"' % (lineNumber+2, sourceFileName))
    simulationContents = ''.join(lines)
  print >> myfile, simulationContents
  myfile.close()
  
  
  from Preferences import CC, CFLAGS, MPICC, MPICFLAGS
  
  prefs = {}
  prefs['CC'] = CC
  prefs['CFLAGS'] = CFLAGS
  prefs['MPICC'] = MPICC
  prefs['MPICFLAGS'] = MPICFLAGS
  
  # Load user preferences. This will be a file called
  # "xpdeint_prefs.py" in ~/.xmds
  preferencesSearchPath = os.path.join(os.environ['HOME'], '.xmds')
  try:
    fd, pathname, description = imp.find_module('xpdeint_prefs', [preferencesSearchPath])
  except ImportError, err:
    # We didn't find the preferences file, no problem.
    pass
  else:
    # We did find the preferences file
    user_prefs = imp.load_module('xpdeint_prefs', fd, pathname, description)
    for prefName in ['CC', 'CFLAGS', 'MPICC', 'MPICFLAGS']:
      if hasattr(user_prefs, prefName):
        prefs[prefName] = getattr(user_prefs, prefName)
  
  CC = prefs['CC']
  CFLAGS = prefs['CFLAGS']
  MPICC = prefs['MPICC']
  MPICFLAGS = prefs['MPICFLAGS']
  
  pathToIncludeDirectory = resource_filename(__name__, 'includes')
  
  CFLAGS += ' -I"%(pathToIncludeDirectory)s"' % locals()
  
  # Now let the templates add anything they need to CFLAGS
  templateCFLAGS = ['']
  # Iterate through all the templates
  for template in globalNameSpace['templates']:
    # If the template has the function 'cflags', then call it, and add it to the list
    if template.hasattr('cflags'):
      templateCFLAGS.append(template.cflags())
    # FIXME: This is very very dodgy
    if template.hasattr('compiler'):
      CC = template.compiler()
  
  # FIXME: DODGY DODGY
  if CC == "mpic++":
    CC = MPICC
    CFLAGS += " " + MPICFLAGS
  
  # These compile variables are defined in Preferences.py
  # We'll need some kind of check to choose which compiler and options, but not until we need varying options
  
  compilerLine = "%(CC)s -o '%(output)s' '%(output)s.cc' %(CFLAGS)s" % locals()
  compilerLine += ' '.join(templateCFLAGS)
  
  if compileScript:
    print "\n",compilerLine,"\n"
  
    proc = subprocess.Popen(compilerLine,
                         shell=True,
                         stdout=subprocess.PIPE,
                         )
    print proc.communicate()[0]
    return proc.wait()
  else:
    # Don't compile the script, but show how we would compile it
    print "\nWould compile with:\n",compilerLine,"\n"

if __name__ == "__main__":
  sys.exit(main())
