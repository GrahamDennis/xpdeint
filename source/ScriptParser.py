#!/usr/bin/env python
# encoding: utf-8
"""
ScriptParser.py

Created by Graham Dennis on 2007-12-29.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import re
from ParserException import ParserException
import RegularExpressionStrings

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
    """
    Return a list of all symbols in `string`.
    
    A 'symbol' is a C language token.
    It can contain underscores, numbers and upper or lower-case characters,
    except for the first character which must be an upper or lower-case 
    character.
    """
    symbolNameRegex = re.compile(r'\b' + RegularExpressionStrings.symbol + r'\b')
    results = symbolNameRegex.findall(string)
    return results
  
  def symbolInString(self, string):
    """
    Return the single symbol in `string`.
    
    If there is more than one symbol in this string (as determined by `symbolsInString`),
    this method will raise a `ValueError` exception.
    """
    results = self.symbolsInString(string)
    if len(results) > 1:
      raise ValueError('Too many symbols')
    elif len(results) == 0:
      raise ValueError('No symbols found')
    else:
      return results[0]
  
  def integersInString(self, string):
    """
    Return a list of the integers in `string`.
    """
    integerRegex = re.compile(r'\b' + RegularExpressionStrings.integer + r'\b')
    results = integerRegex.findall(string)
    # Convert captured strings into integers
    return [int(result) for result in results]
  
  def integerInString(self, string):
    """
    Return the single integer in `string`.
    
    If there is more than one integer in this string (as determined by `integersInString`),
    this method will raise a `ValueError` exception.
    """
    results = self.integersInString(string)
    if len(results) > 1:
      raise ValueError('Too many integers')
    elif len(results) == 0:
      raise ValueError('No integers found')
    return results[0]
  
  def spaceFromStringForFieldInElement(self, spacesString, field, element, globalNameSpace):
    """
    Return the ``space`` bitmask corresponding to `spacesString` for `field`.
    """
    geometryTemplate = globalNameSpace['geometry']
    resultSpace = 0
    
    # Complain if illegal fieldnames or k[integer-valued] are used
    firstFieldName=True
    legalFieldNameString= '\\b('
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
        raise ParserException(element,
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
  
  def targetComponentsForOperatorsInString(self, operatorNames, propagationCode):
    operatorCodeRegex = re.compile(r'\b(' + '|'.join(operatorNames) + ')'+ RegularExpressionStrings.threeLevelsMatchedSquareBrackets, re.VERBOSE)
    return operatorCodeRegex.findall(propagationCode)
  
  def applyAttributeDictionaryToObject(self, attrDict, obj):
    for attrName, attrValue in attrDict.iteritems():
      obj.__setattr__(attrName, attrValue)
    
  
  def domainPairFromString(self, domainString, numberType, element):
    """
    Parse a string of the form ``(someNumber1, someNumber2)`` and return the two
    strings corresponding to the numbers ``someNumber1`` and ``someNumber2`` making
    sure that ``someNumber1`` is less than ``someNumber2``.
    
    `numberType` is the class to which the strings ``someNumber1`` and ``someNumber2`` will
    be converted to ensure the ordering of the numbers.
    """
    
    regex = re.compile(RegularExpressionStrings.domainPair)
    result = regex.match(domainString)
    if not result:
      raise ParserException(element, "Could not understand '%(domainString)s' as a domain"
                                     " of the form ( +/-someNumber, +/-someNumber)" % locals())
    
    minimumString = result.group(1)
    maximumString = result.group(2)
    
    def validateNumberString(string):
      try:
        value = numberType(string)
      except ValueError, err:
        raise ParserException(element, "Could not understand '%(string)s' as a number." % locals())
    
    
    validateNumberString(minimumString)
    validateNumberString(maximumString)
    
    if numberType(minimumString) >= numberType(maximumString):
      raise ParserException(element, "The end point of the dimension '%(maximumString)s' must be "
                                     "greater than the start point '%(minimumString)s'." % locals())
    
    return minimumString, maximumString
    
