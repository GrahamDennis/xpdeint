#!/usr/bin/env python
# encoding: utf-8
"""
ScriptParser.py

Created by Graham Dennis on 2007-12-29.

Copyright (c) 2007-2012, Graham Dennis

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of The Australian National University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

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
    

