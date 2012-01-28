#!/usr/bin/env python
# encoding: utf-8
"""
minidom_extras.py

Created by Graham Dennis on 2008-06-15.

Copyright (c) 2008-2012, Graham Dennis

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of The Australian National University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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


def install_minidom_extras():
  """
  This is the function to call to get the minidom extras installed.
  """
  # Add the helper methods defined earlier to the XML classes
  minidom.Element.getChildElementsByTagName  = getChildElementsByTagName
  minidom.Document.getChildElementsByTagName = getChildElementsByTagName
  
  minidom.Element.getChildElementByTagName  = getChildElementByTagName
  minidom.Document.getChildElementByTagName = getChildElementByTagName
  minidom.Document.createCDATASection = composeFunctions(minidom.Document.createCDATASection, setLineNumberForCDATASection)
  
  minidom.Element.innerText = innerText
  minidom.Element.cdataContents = cdataContents
  minidom.Element.lineNumberForCDATASection = lineNumberForCDATASection
  minidom.Element.userUnderstandableXPath = userUnderstandableXPath
  
  # Add our setLineAndColumnHandlers function to the end of the 'reset' function of ExpatBuilder
  # This will ensure that our line and column number handlers are installed when any ExpatBuilder
  # instance is created. This gets us line and column number information on our XML nodes as minidom
  # uses ExpatBuilder to do the parsing for it.
  # Note that 'reset' gets called during initialisation of the ExpatBuilder.
  expatbuilder.ExpatBuilder.install = concatenateFunctions(setLineAndColumnHandlers, expatbuilder.ExpatBuilder.install)
  

install_minidom_extras()
