#!/usr/bin/env python
# encoding: utf-8
"""
PrintfSafeFilter.py

Created by Graham Dennis on 2007-09-23.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from Cheetah.Filters import Filter

class PrintfSafeFilter(Filter):
  """Escape C string and format string entities in $placeholders
  """
  def filter(self, val, **kw):
    s = super(PrintfSafeFilter, self).filter(val, **kw)
    s = s.replace("\\", "\\\\")   # Escape single backslashes
    s = s.replace("%", "%%")      # Escape format-string specifiers
    s = s.replace("\"", "\\\"")   # Escape double-quotes
    ## We're done
    return s
