#!/usr/bin/env python
# encoding: utf-8
"""
RegularExpressionStrings.py

Created by Graham Dennis on 2008-02-20.

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
import re

# integer regular expression string
integer = r'[-+]?[0-9]+'

# domain pair ( something, somethingElse) regular expression string
domainPair = r'\(\s*(\S+),\s*(\S+)\s*\)'

def integersInString(string):
  """
  Return a list of the integers in `string`.
  """
  integerRegex = re.compile(r'\b' + integer + r'\b')
  results = integerRegex.findall(string)
  # Convert captured strings into integers
  return [int(result) for result in results]

def integerInString(string):
  """
  Return the single integer in `string`.
  
  If there is more than one integer in this string (as determined by `integersInString`),
  this method will raise a `ValueError` exception.
  """
  results = integersInString(string)
  if len(results) > 1:
    raise ValueError('Too many integers')
  elif len(results) == 0:
    raise ValueError('No integers found')
  return results[0]
  
