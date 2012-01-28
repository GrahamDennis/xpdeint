#!/usr/bin/env python
# encoding: utf-8
"""
RegularExpressionStrings.py

Created by Graham Dennis on 2008-02-20.

Copyright (c) 2008-2012, Graham Dennis

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of The Australian National University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
  
