#!/usr/bin/env python
# encoding: utf-8
"""
ParserException.py

Created by Graham Dennis on 2007-10-14.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import sys

class ParserException(Exception):
  def __init__(self, element, msg):
    self.msg = msg
    self.element = element


def parserWarning(element, msg):
  lineNumber = element.getUserData('lineNumber')
  columnNumber = element.getUserData('columnNumber')
  print >> sys.stderr, "Warning: " + msg
  print >> sys.stderr, "    At line %(lineNumber)i, column %(columnNumber)i" % locals()
  # print >> sys.stderr, "    In element: " + element.userUnderstandableXPath()

