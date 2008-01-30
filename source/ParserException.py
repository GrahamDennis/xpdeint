#!/usr/bin/env python
# encoding: utf-8
"""
ParserException.py

Created by Graham Dennis on 2007-10-14.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import inspect
import os
import sys

class ParserException(Exception):
  def __init__(self, element, msg):
    self.msg = msg
    self.element = element
    
    callerFrame = sys._getframe(1)
    self.sourceFileName = os.path.basename(inspect.getfile(callerFrame))
    self.sourceFileLineNumber = inspect.getlineno(callerFrame)
    del callerFrame

