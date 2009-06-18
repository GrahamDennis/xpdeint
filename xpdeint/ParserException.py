#!/usr/bin/env python
# encoding: utf-8
"""
ParserException.py

Created by Graham Dennis on 2007-10-14.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import sys
import textwrap

def indentMessageWithPrefix(prefix, msg):
    textWrapper = textwrap.TextWrapper(subsequent_indent=' '*len(prefix))
    return textWrapper.fill(prefix + msg)


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

