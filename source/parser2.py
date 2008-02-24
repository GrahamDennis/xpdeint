#!/usr/bin/env python
# encoding: utf-8
"""
parser2.py

Created by Graham Dennis on 2008-01-03.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

import sys
import getopt
from xml.dom import minidom
import subprocess

# Hack for Leopard so it doesn't import the web rendering
# framework WebKit when Cheetah tries to import the Python
# web application framework WebKit
if sys.platform == 'darwin':
  import new
  sys.modules['WebKit'] = new.module('WebKit')


# Import the parser stuff
from ParserException import ParserException
from XMDS2Parser import XMDS2Parser

# Import the top level template
from Simulation import Simulation as SimulationTemplate

# Import the IndentFilter. The IndentFilter is the magic filter
# that when used correctly makes the generated source correctly
# indented. See the comments in IndentFilter.py for more info.
from IndentFilter import IndentFilter

# Import the root class for all templates
from _ScriptElement import _ScriptElement

# The help message printed when --help is used as an argument
help_message = '''
usage: parser2 [options] fileToBeParsed

Options and arguments:
-h          : Print this message (also --help)
-o filename : This overrides the name of the output file to be generated
-v          : Verbose mode (also --verbose)
'''


# These are additional functions that will be added to the XML
# classes for convenience.
def getChildElementsByTagName(self, tagName, optional=False):
  """
  Return child XML elements that have the tag name `tagName`.
  
  This function will raise an exception if there are no children
  with `tagName` unless the keyword argument `optional` is passed
  with a value of `True`.
  """
  
  elements = filter(lambda x: x.nodeType == minidom.Node.ELEMENT_NODE and x.tagName == tagName, self.childNodes)
  if not optional and len(elements) == 0:
    raise ParserException(self, "There must be at least one '" + tagName + "' element.")
  return elements


def getChildElementByTagName(self, tagName, optional=False):
  """
  Return the child XML element that has the tag name `tagName`.
  
  This function will raise an exception if there is more than
  one child with tag name `tagName`. Unless the keyword argument
  `optional` is passed with a value of `True`, an exception will
  also be raised if there is no child with tag name `tagName`.
  """
  elements = self.getChildElementsByTagName(tagName, optional=optional)

  if not optional and not len(elements) == 1:
    raise ParserException(self, "There should one and only be one '" + tagName + "' element.")

  if optional and len(elements) > 1:
    raise ParserException(self, "There should be no more than one '" + tagName + "' element.")

  if optional and len(elements) == 0:
    return None
  else:
    return elements[0]


def innerText(self):
  """
  Return the contents of all descendent text nodes and CDATA nodes.
  
  For example, consider the following XML::
  
    <root>
      <someTag> someText </someTag>
      <![CDATA[
        some other text.
        ]]>
    </root>
  
  On the ``root`` element, `innerText` would return " someText some other text." plus
  or minus some newlines and other whitespace.
  """
  contents = []
  for child in self.childNodes:
    if child.nodeType == minidom.Node.ELEMENT_NODE:
      contents.append(child.innerText())
    elif child.nodeType == minidom.Node.TEXT_NODE or child.nodeType == minidom.Node.CDATA_SECTION_NODE:
      contents.append(child.data)
  return "".join(contents).strip()


def cdataContents(self):
  """
  Return the contents of any CDATA nodes that are children of this element.
  """
  contents = []
  for child in self.childNodes:
    if child.nodeType == minidom.Node.CDATA_SECTION_NODE:
      contents.append(child.data)
  return "".join(contents)

def userUnderstandableXPath(self):
  """
  Return an XPath-like string (but more user-friendly) which allows the user to
  locate this XML element.
  
  I'd use line/column numbers too except that that information isn't available as part
  of the XML spec, so there isn't any function that you can call on an element to get
  that information. At least from what I can tell.
  """
  
  currentElement = self
  elementPath = []
  
  while 1:
    if not currentElement:
      break
    elementPath.append(currentElement)
    currentElement = currentElement.parentNode
  
  elementPathStringList = []
  for currentElement in reversed(elementPath):
    if len(elementPathStringList) > 0:
      elementPathStringList.append(" --> ")
    
    elementDescription = currentElement.nodeName
    
    if currentElement.parentNode:
      siblingElements = currentElement.parentNode.getChildElementsByTagName(currentElement.tagName)
      if len(siblingElements) > 1:
        elementDescription += '[' + str(siblingElements.index(currentElement)) + ']'
    elementPathStringList.extend(["'", elementDescription, "'"])
  
  return ''.join(elementPathStringList)


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
  # If verbose is true, then when an error occurs during parsing,
  # the Python backtrace will be shown in addition to the XML location
  # where the error occurred.
  verbose = False
  
  # Attempt to parse command line arguments
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.gnu_getopt(argv[1:], "ho:v", ["help", "output="])
    except getopt.error, msg:
      raise Usage(msg)
    
    output=''
    # option processing
    for option, value in opts:
      if option == "-v":
        verbose = True
      if option in ("-h", "--help"):
        raise Usage(help_message)
      if option in ("-o", "--output"):
        output = value
    
    # argument processing
    if len(args)==1:
        scriptName = args[0]
    else:
        raise Usage(help_message)
  
  except Usage, err:
    print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
    print >> sys.stderr, "\t for help use --help"
    return 2
    
  # Add the helper methods defined earlier to the XML classes
  minidom.Element.getChildElementsByTagName  = getChildElementsByTagName
  minidom.Document.getChildElementsByTagName = getChildElementsByTagName
  
  minidom.Element.getChildElementByTagName  = getChildElementByTagName
  minidom.Document.getChildElementByTagName = getChildElementByTagName
  
  minidom.Element.innerText = innerText
  minidom.Element.cdataContents = cdataContents
  minidom.Element.userUnderstandableXPath = userUnderstandableXPath
  
  
  # globalNameSpace is a dictionary of variables that are available in all
  # templates
  globalNameSpace = {}
  
  
  # Open the script file
  scriptFile = file(scriptName)
  # Read the contents of the file
  globalNameSpace['inputScript'] = scriptFile.read()
  # Close the file
  scriptFile.close()
  del scriptFile
  
  # Parse the XML input script into a set of XML
  # classes
  xmlDocument = minidom.parse(scriptName)
  
  # Set up the globalNameSpace with the appropriate variables
  globalNameSpace['xmlDocument'] = xmlDocument
  globalNameSpace['scriptElements'] = []
  globalNameSpace['features'] = {}
  globalNameSpace['fields'] = []
  globalNameSpace['vectors'] = []
  globalNameSpace['momentGroups'] = []
  globalNameSpace['symbolNames'] = set()
  globalNameSpace['xmds'] = {'versionString': '0.0a',
                             'subversionRevision': 'rF00'}
  globalNameSpace['templates'] = set()
  
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
    simulationTemplate = SimulationTemplate(searchList=[globalNameSpace], filter=filterClass)
    # Now get the parser to do the complex job of mapping the XML classes onto our
    # templates.
    simulationTemplate.simulation = parser.parseXMLDocument(xmlDocument, globalNameSpace, filterClass)
    
    # Now run preflight stage
    # Preflight is the stage which maps vector names, etc to the actual vectors themselves. It also
    # allows all templates to check that all of their settings are sane, and raise an exception if
    # there is a problem.
    #
    # FIXME: While this works, I don't believe it is the best design
    # Instead of having these somewhat arbitrary 'scriptElements', they should all be set
    # as children of the SimulationElement, and the SimulationElement should be set as a child of
    # the Simulation.
    # FIXME: Actually, I'm not so fond of the Simulation / SimulationElement distinction. They should be combined.
    
    # Loop over a copy because we may create templates during iteration
    for template in globalNameSpace['templates'].copy():
      template.createNamedVectors()
    
    for template in globalNameSpace['templates'].copy():
      template.bindNamedVectors()
    
    for template in globalNameSpace['templates'].copy():
      template.preflight()
    
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
    print >> sys.stderr, "Error: " + err.msg
    print >> sys.stderr, "    In element: " + err.element.userUnderstandableXPath()
    print >> sys.stderr, "For a complete traceback, pass -v on the command line."
    
    # If we have the verbose option on, then in addition to the path to the XML element
    # that triggered the exception, print a traceback showing the list of Python function
    # calls that led to the exception being hit.
    if verbose:
      raise
    
    return -1
  
  # Now actually write the simulation to disk.
  
  if output == '':
    output = globalNameSpace['simulationName']
  myfile = file(output + ".cc", "w")
  print >> myfile, simulationTemplate
  myfile.close()
  
  
  from Preferences import CC,CFLAGS
  
  # Now let the templates add anything they need to CFLAGS
  templateCFLAGS = ['']
  # Iterate through all the templates
  for template in globalNameSpace['templates']:
    # If the template has the function 'cflags', then call it, and add it to the list
    if template.hasattr('cflags'):
      templateCFLAGS.append(template.cflags())
  
  
  # These compile variables are defined in Preferences.py
  # We'll need some kind of check to choose which compiler and options, but not until we need varying options
  
  compilerLine = CC + " -o " + output + " " + output + ".cc " + CFLAGS + ' '.join(templateCFLAGS)
  print "\n",compilerLine,"\n"
  
  proc = subprocess.Popen(compilerLine,
                       shell=True,
                       stdout=subprocess.PIPE,
                       )
  print proc.communicate()[0]
  return proc.wait()

if __name__ == "__main__":
  sys.exit(main())
