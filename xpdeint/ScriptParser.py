#!/usr/bin/env python
# encoding: utf-8
"""
ScriptParser.py

Created by Graham Dennis on 2007-12-29.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import re
from xpdeint import RegularExpressionStrings

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
            setattr(obj, attrName, attrValue)
    

