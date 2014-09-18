#!/usr/bin/env python
# encoding: utf-8
"""
ParserException.py

Created by Graham Dennis on 2007-10-14.

Copyright (c) 2007-2012, Graham Dennis

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

import sys
import textwrap

def indentMessageWithPrefix(prefix, msg):
    textWrapper = textwrap.TextWrapper(subsequent_indent=' '*len(prefix))
    msgLines = msg.split('\n\n')
    result = [textWrapper.fill(prefix + msgLines[0])]
    textWrapper.initial_indent = ' '*len(prefix)
    result.extend([textWrapper.fill(line) for line in msgLines[1:]])
    return '\n'.join(result)

def error_missing_python_library(library_name, xmlElement = None):
  raise ParserException(xmlElement, "This script requires the python package '%s' which is not installed.  Please install it to run this script." % library_name)

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

