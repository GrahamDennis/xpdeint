#!/usr/bin/env python
# encoding: utf-8
"""
ParsedEntity.py

Created by Graham Dennis on 2008-01-01.

Copyright (c) 2008-2012, Graham Dennis

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

from xpdeint.Utilities import lazy_property

class ParsedEntity(object):
  def __init__(self, xmlElement, value):
    self.xmlElement = xmlElement
    self.value = value
  
  @lazy_property
  def scriptLineNumber(self):
    return self.xmlElement.lineNumberForCDATASection()
  

