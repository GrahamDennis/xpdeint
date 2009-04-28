#!/usr/bin/env python
# encoding: utf-8
"""
ParsedEntity.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Utilities import lazy_property

class ParsedEntity(object):
  def __init__(self, xmlElement, value):
    self.xmlElement = xmlElement
    self.value = value
  
  @lazy_property
  def scriptLineNumber(self):
    return self.xmlElement.lineNumberForCDATASection()
  

