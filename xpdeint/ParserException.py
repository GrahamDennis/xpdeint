#!/usr/bin/env python
# encoding: utf-8
"""
ParserException.py

Created by Graham Dennis on 2007-10-14.

Copyright (c) 2007-2012, Graham Dennis

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of The Australian National University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import sys
import textwrap

def indentMessageWithPrefix(prefix, msg):
    textWrapper = textwrap.TextWrapper(subsequent_indent=' '*len(prefix))
    msgLines = msg.split('\n\n')
    result = [textWrapper.fill(prefix + msgLines[0])]
    textWrapper.initial_indent = ' '*len(prefix)
    result.extend([textWrapper.fill(line) for line in msgLines[1:]])
    return '\n'.join(result)


class ParserException(Exception):
    def __init__(self, element, msg):
        
        self.msg = indentMessageWithPrefix('ERROR: ', msg)
        self.element = element
        
        self.lineNumber = self.columnNumber = None
        
        if self.element:
            self.lineNumber = self.element.getUserData('lineNumber')
            self.columnNumber = self.element.getUserData('columnNumber')

warningsGiven = set()

def parserWarning(element, msg):
    try:
        lineNumber, columnNumber = element
    except (TypeError, ValueError), err:
        lineNumber = element.getUserData('lineNumber')
        columnNumber = element.getUserData('columnNumber')
    if (lineNumber, columnNumber, msg) in warningsGiven: return
    warningsGiven.add((lineNumber, columnNumber, msg))
    print >> sys.stderr, indentMessageWithPrefix('WARNING: ', msg)
    print >> sys.stderr, "    At line %(lineNumber)i, column %(columnNumber)i" % locals()
    # print >> sys.stderr, "    In element: " + element.userUnderstandableXPath()

