#!/usr/bin/env python
# encoding: utf-8
"""
RegularExpressionStrings.py

Created by Graham Dennis on 2008-02-20.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
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
  
