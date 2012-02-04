#!/usr/bin/env python
# encoding: utf-8
"""
PrintfSafeFilter.py

Created by Graham Dennis on 2007-09-23.

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

from Cheetah.Filters import Filter

class PrintfSafeFilter(Filter):
  """Escape C string and format string entities in $placeholders
  """
  def filter(self, val, **kw):
    s = super(PrintfSafeFilter, self).filter(val, **kw)
    s = s.replace("\\", "\\\\")   # Escape single backslashes
    s = s.replace("%", "%%")      # Escape format-string specifiers
    s = s.replace("\"", "\\\"")   # Escape double-quotes
    # We're done
    return s
