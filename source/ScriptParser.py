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
    geometryTemplate = globalNameSpace['geometry']
    resultSpace = 0

    # Complain if illegal fieldnames or k[integer-valued] are used
    firstFieldName=True
    legalFieldNameString='\\b('
    for fieldDimension in field.dimensions:
        if not firstFieldName:
	       legalFieldNameString+='|'
        if fieldDimension.type=='double':
            legalFieldNameString+='k'+fieldDimension.name+'|'+fieldDimension.name
        else:
            legalFieldNameString+=fieldDimension.name            
        firstFieldName=False
    legalFieldNameString+=r')\b'
    legalRegex = re.compile(legalFieldNameString)

    for symbol in self.symbolsInString(spacesString):
        if len(legalRegex.findall(symbol))!=1:
            raise 	ParserException(element,
		              "The fourier_space string must only contain real-valued dimensions from the"
                      "designated field.  '%(symbol)s' cannot be used."  % locals())
    
    for dimensionNumber, fieldDimension in enumerate(field.dimensions):
        if fieldDimension.transverse and fieldDimension.type=='double':
           fieldDimName = fieldDimension.name
           spacesOptionsString=r'\b('+'k'+fieldDimName+'|'+fieldDimName+r')\b'
           spacesRegex = re.compile(spacesOptionsString)
           spaces = spacesRegex.findall(spacesString)
           if not len(spaces) == 1:
		      raise ParserException(element,
		              "The fourier_space attribute must have exactly one entry of either"
                      "'k%(fieldDimName)s' or '%(fieldDimName)s'."  % locals()) 
           elif spaces[0] == 'k'+fieldDimName:
		         resultSpace |= 1 << geometryTemplate.indexOfDimension(field.dimensions[dimensionNumber])
    
    return resultSpace
  
  def targetComponentsForOperatorInString(self, operatorName, propagationCode):
    operatorCodeRegex = re.compile(r'\b' + operatorName + r'\[\s*(.+)\s*\]')
    return operatorCodeRegex.findall(propagationCode)
  
  def applyAttributeDictionaryToObject(self, attrDict, obj):
    for attrName, attrValue in attrDict.iteritems():
      obj.__setattr__(attrName, attrValue)
    
  
