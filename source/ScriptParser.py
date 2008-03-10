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
    
