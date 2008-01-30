#!/usr/bin/env python
# encoding: utf-8
"""
ScriptParser.py

Created by Graham Dennis on 2007-12-29.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import re
from ParserException import ParserException

## Subclasses for parsing specific scripts types should
## override the following functions:
##
### canParseXMLDocument
### -- return whether the subclass can parse the document
### parseXMLDocument
### --- return the top-level SimulationElement after parsing
###     the script.

class ScriptParser(object):
  def canParseXMLDocument(self, xmlDocument):
    return False
  
  def parseXMLDocument(self, xmlDocument, globalNameSpace):
    return None
  
  def symbolsInString(self, string):
    symbolNameRegex = re.compile(r'\b[a-zA-Z]\w*\b')
    results = symbolNameRegex.findall(string)
    return results
  
  def symbolInString(self, string):
    results = self.symbolsInString(string)
    if len(results) > 1:
      raise ValueError('Too many symbols')
    elif len(results) == 0:
      raise ValueError('No symbols found')
    else:
      return results[0]
  
  def integersInString(self, string):
    integerRegex = re.compile(r'\b[-+]?[0-9]+\b')
    results = integerRegex.findall(string)
    # Convert captured strings into integers
    return [int(result) for result in results]
  
  def integerInString(self, string):
    results = self.integersInString(string)
    if len(results) > 1:
      raise ValueError('Too many integers')
    elif len(results) == 0:
      raise ValueError('No integers found')
    return results[0]
  
  def spaceFromStringForFieldInElement(self, spacesString, field, element, globalNameSpace):
    spacesRegex = re.compile(r'\b(yes|no|k|x)\b')
    spaces = spacesRegex.findall(spacesString.lower())
    
    if not len(spaces) == len(field.dimensions):
      raise ParserException(element, 
              "The fourier_space attribute must have the same number of yes/no/k/x "
              "entries as the source_field has dimensions.")
    
    geometryTemplate = globalNameSpace['geometry']
    resultSpace = 0
    for dimensionNumber, space in enumerate(spaces):
      if space == 'yes' or space == 'k':
        resultSpace |= 1 << geometryTemplate.indexOfDimension(field.dimensions[dimensionNumber])
    return resultSpace
  
  def targetComponentsForOperatorInString(self, operatorName, propagationCode):
    operatorCodeRegex = re.compile(r'\b' + operatorName + r'\[\s*(.+)\s*\]')
    return operatorCodeRegex.findall(propagationCode)
  
