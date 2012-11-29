#!/usr/bin/env python
# encoding: utf-8
"""
minidom_extras.py

Created by Graham Dennis on 2008-06-15.

Copyright (c) 2008-2012, Graham Dennis

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

from xml.dom import minidom
from xml.dom import expatbuilder
from xpdeint.ParserException import ParserException
import xpdeint.Python24Support

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
    raise ParserException(self, "There must be at least one '%(tagName)s' element." % locals())
  return elements

def getChildElementsByTagNames(self, tagNames, optional=False):
  """
  Return child XML elements that have tag names in the collection `tagNames`.
  
  This function will raise an exception if there are no children with a tag name in `tagNames`
  unless the keyword argument `optional` is `True`.
  """
  
  elements = [element for element in self.childNodes if element.nodeType == minidom.Node.ELEMENT_NODE and element.tagName in tagNames]
  if not optional and len(elements) == 0:
    raise ParserException(self, "There must be at least one element from the set {%s}." % ", ".join(tagNames))
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
    raise ParserException(self, "There must be exactly one '%(tagName)s' element." % locals())

  if optional and len(elements) > 1:
    raise ParserException(self, "There may be at most one '%(tagName)s' element." % locals())

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

def lineNumberForCDATASection(self):
  for child in self.childNodes:
    if child.nodeType == minidom.Node.CDATA_SECTION_NODE:
      return child.getUserData('lineNumber')
  raise ParserException(self, "Missing CDATA section.")

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

from functools import wraps

def concatenateFunctions(f1, f2):
  """
  Returns a function that calls two functions in turn.
  
  The function returned by this function first calls `f1`, and then
  `f2`, but returns the result of `f1`.
  """
  @wraps(f1)
  def wrapper(*args, **KWs):
    result = f1(*args, **KWs)
    f2(*args, **KWs)
    return result
  
  return wrapper

def composeFunctions(f1, f2):
  """
  Returns a function that calls ``f2(f1(args))``.
  """
  @wraps(f1)
  def wrapper(*args, **KWs):
    return f2(f1(*args, **KWs))
  
  return wrapper

def setLineAndColumnHandlers(self, *argsOuter, **KWsOuter):
  """
  Set the line and column number handlers for an ExpatBuilder.
  """
  def setLineAndColumnValuesForElement(*args, **KWs):
    """
    Set the line and column numbers from the expat parser.
    This data is copied into the ``userData`` dictionary of the node.
    The start of the XML tag's line number is available with the key
    'lineNumber', and its column number with the key 'columnNumber'.
    """
    parser = self._parser
    self.curNode.setUserData('lineNumber', parser.CurrentLineNumber, None)
    self.curNode.setUserData('columnNumber', parser.CurrentColumnNumber, None)
  
  def getLineNumberForCDATASection(*args, **KWs):
    parser = self._parser
    self.curNode.ownerDocument.setUserData('_cdata_section_line_number_start', parser.CurrentLineNumber, None)
  
  self.start_element_handler = concatenateFunctions(self.start_element_handler, setLineAndColumnValuesForElement)
  self.start_cdata_section_handler = concatenateFunctions(self.start_cdata_section_handler, getLineNumberForCDATASection)

def setLineNumberForCDATASection(node):
  node.setUserData('lineNumber', node.ownerDocument.getUserData('_cdata_section_line_number_start'), None)
  return node

def external_entity_ref_handler(self, context, base, systemId, publicId):
  childParser = self._parser.ExternalEntityParserCreate(context)
  fragment = self.document.createDocumentFragment()
  childParser.Parse(open(systemId,'r').read(), 1)
  
  return 1

def install_minidom_extras():
  """
  This is the function to call to get the minidom extras installed.
  """
  # Add the helper methods defined earlier to the XML classes
  minidom.Element.getChildElementsByTagName  = getChildElementsByTagName
  minidom.Document.getChildElementsByTagName = getChildElementsByTagName
  
  minidom.Element.getChildElementsByTagNames  = getChildElementsByTagNames
  minidom.Document.getChildElementsByTagNames = getChildElementsByTagNames
  
  minidom.Element.getChildElementByTagName  = getChildElementByTagName
  minidom.Document.getChildElementByTagName = getChildElementByTagName
  
  minidom.Document.createCDATASection = composeFunctions(minidom.Document.createCDATASection, setLineNumberForCDATASection)
  
  minidom.Element.innerText = innerText
  minidom.Element.cdataContents = cdataContents
  minidom.Element.lineNumberForCDATASection = lineNumberForCDATASection
  minidom.Element.userUnderstandableXPath = userUnderstandableXPath
  

  expatbuilder.ExpatBuilder.external_entity_ref_handler = external_entity_ref_handler
  
  
  # Add our setLineAndColumnHandlers function to the end of the 'reset' function of ExpatBuilder
  # This will ensure that our line and column number handlers are installed when any ExpatBuilder
  # instance is created. This gets us line and column number information on our XML nodes as minidom
  # uses ExpatBuilder to do the parsing for it.
  # Note that 'reset' gets called during initialisation of the ExpatBuilder.
  expatbuilder.ExpatBuilder.install = concatenateFunctions(setLineAndColumnHandlers, expatbuilder.ExpatBuilder.install)
  

install_minidom_extras()
