#!/usr/bin/env python
# encoding: utf-8
"""
parser2.py

Created by Graham Dennis on 2008-01-03.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import sys
import getopt
from xml.dom import minidom

# Hack for Leopard so it doesn't import the web rendering
# framework WebKit when Cheetah tries to import the Python
# web application framework WebKit
if sys.platform == 'darwin':
  import new
  sys.modules['WebKit'] = new.module('WebKit')

from ParserException import ParserException
from XMDS2Parser import XMDS2Parser

from Simulation import Simulation as SimulationTemplate

from IndentFilter import IndentFilter

help_message = '''
The help message goes here.
'''

def getChildElementsByTagName(self, tagName, optional=False):
  elements = filter(lambda x: x.nodeType == minidom.Node.ELEMENT_NODE and x.tagName == tagName, self.childNodes)
  if not optional and len(elements) == 0:
    raise ParserException(self, "There must be at least one '" + tagName + "' element.")
  return elements


def getChildElementByTagName(self, tagName, optional=False):
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
  contents = []
  for child in self.childNodes:
    if child.nodeType == minidom.Node.ELEMENT_NODE:
      contents.append(child.innerText())
    elif child.nodeType == minidom.Node.TEXT_NODE or child.nodeType == minidom.Node.CDATA_SECTION_NODE:
      contents.append(child.data)
  return "".join(contents).strip()


def cdataContents(self):
  contents = []
  for child in self.childNodes:
    if child.nodeType == minidom.Node.CDATA_SECTION_NODE:
      contents.append(child.data)
  return "".join(contents)


# Function to return an (any) object from an iterable, though designed to be used with sets
def anyObject(iterable):
  for obj in iterable:
    return obj


class Usage(Exception):
  def __init__(self, msg):
    self.msg = msg


def main(argv=None):
  verbose = False
  if argv is None:
    argv = sys.argv
  try:
    try:
      opts, args = getopt.getopt(argv[1:], "ho:v", ["help", "output="])
    except getopt.error, msg:
      raise Usage(msg)
    
    # option processing
    for option, value in opts:
      if option == "-v":
        verbose = True
      if option in ("-h", "--help"):
        raise Usage(help_message)
      if option in ("-o", "--output"):
        output = value
  
  except Usage, err:
    print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
    print >> sys.stderr, "\t for help use --help"
    return 2
  
  scriptName = "../examples/kubo.xmds"
  
  minidom.Element.getChildElementsByTagName  = getChildElementsByTagName
  minidom.Document.getChildElementsByTagName = getChildElementsByTagName
  
  minidom.Element.getChildElementByTagName  = getChildElementByTagName
  minidom.Document.getChildElementByTagName = getChildElementByTagName
  
  minidom.Element.innerText = innerText
  minidom.Element.cdataContents = cdataContents
  
  globalNameSpace = {}
  
  scriptFile = file(scriptName)
  globalNameSpace['inputScript'] = scriptFile.read()
  scriptFile.close()
  del scriptFile
  
  xmlDocument = minidom.parse(scriptName)
  
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
  
  globalNameSpace['anyObject'] = anyObject
  
  try:
    parser = None
    if XMDS2Parser.canParseXMLDocument(xmlDocument):
      parser = XMDS2Parser()
    
    if not parser:
      print >> sys.stderr, "Unable to recognise file as an xmds script."
      return
    
    filterClass = IndentFilter
    simulationTemplate = SimulationTemplate(searchList=[globalNameSpace], filter=filterClass)
    globalNameSpace['scriptElements'].append(simulationTemplate)
    simulationTemplate.simulation = parser.parseXMLDocument(xmlDocument, globalNameSpace, filterClass)
    
    # Now run preflight stage
    # FIXME: While this works, I don't believe it is the best design
    # Instead of having these somewhat arbitrary 'scriptElements', they should all be set
    # as children of the SimulationElement, and the SimulationElement should be set as a child of
    # the Simulation.
    # FIXME: Actually, I'm not so fond of the Simulation / SimulationElement distinction. They should be combined.
    
    # So the idea here is that each template that has a preflight, but it may not want to execute it until
    # something else has happened in preflight. So we check if each template can run its preflight, and then run it
    # If it can't, then we schedule it to run later. If nothing is executed in a whole loop, and we still have stuff
    # to execute, then we have reached a dead-lock, so we exit.
    
    delayedPreflights = set()
    preflights = set(globalNameSpace['templates'])
    
    while len(preflights):
      for template in preflights:
        if hasattr(template, 'preflight'):
          if not template.canRunPreflightYet():
            delayedPreflights.add(template)
          else:
            template.preflight()
      
      if len(preflights) == len(delayedPreflights):
        # If this is true, then everything opted to be delayed.
        # This means we have a deadlock
        raise Exception("Deadlock in preflight. Classes involved: %s" % preflights)
      preflights = delayedPreflights.copy()
      delayedPreflights = set()
    
  except ParserException, err:  
    elementPath = []
    currentElement = err.element
    while 1:
      if not currentElement:
        break
      elementPath.append(currentElement)
      currentElement = currentElement.parentNode
    
    elementPathString = ""
    for currentElement in reversed(elementPath):
      if len(elementPathString) > 0:
        elementPathString += " --> "
      
      elementDescription = currentElement.nodeName
      
      if currentElement.parentNode:
        siblingElements = currentElement.parentNode.getChildElementsByTagName(currentElement.tagName)
        if len(siblingElements) > 1:
          elementDescription += '[' + str(siblingElements.index(currentElement)) + ']'
      elementPathString = elementPathString + "'" + elementDescription + "'"
    
    print >> sys.stderr, "Error: " + err.msg
    print >> sys.stderr, "    In element: " + elementPathString
    print >> sys.stderr, "For a complete traceback, pass -v on the command line."
    
    if verbose:
      raise
    
    return -1
  
  del globalNameSpace['vectors']
  
  print simulationTemplate


if __name__ == "__main__":
  sys.exit(main())
