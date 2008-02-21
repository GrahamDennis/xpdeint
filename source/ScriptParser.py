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
    
    The contents of `spacesString` must be a sequence of dimension names or fourier
    space versions of those dimension names (i.e. the dimension name prefixed with a 'k')
    where legal.
    
    For example, if the geometry has dimensions 'x', 'y', 'z' and 'u', where 'u' is an
    integer-valued dimension, then the following are valid entries in `spacesString`:
    'x', 'kx', 'y', 'ky', 'z' and 'u'.
    
    Note that the entries in `spacesString` do not need to be in any order.
    """
    geometryTemplate = globalNameSpace['geometry']
    resultSpace = 0
    
    # Complain if illegal fieldnames or k[integer-valued] are used
    legalDimensionNames = set()
    for fieldDimension in field.dimensions:
      legalDimensionNames.add(fieldDimension.name)
      # If the dimension is of type 'double', then we may be
      # fourier transforming it.
      if fieldDimension.type == 'double':
        legalDimensionNames.add('k' + fieldDimension.name)
    
    spacesSymbols = self.symbolsInString(spacesString)
    
    for symbol in spacesSymbols:
      if not symbol in legalDimensionNames:
        raise ParserException(element, 
                "The fourier_space string must only contain real-valued dimensions from the\n"
                "designated field.  '%(symbol)s' cannot be used."  % locals())
    
    for dimensionNumber, fieldDimension in enumerate(field.dimensions):
      fieldDimensionName = fieldDimension.name
      validDimensionNamesForField = set([fieldDimensionName])
      if fieldDimension.type == 'double':
        validDimensionNamesForField.add('k' + fieldDimensionName)
      
      dimensionOccurrences = sum([spacesSymbols.count(dimName) for dimName in validDimensionNamesForField])
      
      if dimensionOccurrences > 1:
        raise ParserException(element,
                  "The fourier_space attribute must only have one entry for dimension '%(fieldDimensionName)s'." % locals())
      elif dimensionOccurrences == 0 and fieldDimension.type == 'double':
        raise ParserException(element,
                  "The fourier_space attribute must have an entry for dimension '%(fieldDimensionName)s'." % locals())
      
      if fieldDimension.type == 'double' and ('k' + fieldDimensionName) in spacesSymbols:
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
    
