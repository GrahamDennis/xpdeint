#!/usr/bin/env python
# encoding: utf-8
"""
RegularExpressionStrings.py

Created by Graham Dennis on 2008-02-20.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

threeLevelsMatchedSquareBrackets = r'''
\[ # Match initial opening square bracket
    
    # Now make a named group 'innerContents' to capture the contents
    # of the square brackets
    (?P<innerContents>
      # Create non-capturing group for repetition
      (?:
        # A balanced substring is either something that is not
        # square brackets:
        [^\[\]]
        | # ... or square brackets surrounding a balanced substring
        \[ # Opening bracket for second level of balanced square brackets
          # Non-capturing group for repetition
          (?:
            [^\[\]]
            |
            \[ # Opening bracket for third level of balanced square brackets
              [^\[\]]*
            \] # Closing bracket for third level of balanced square brackets
          )*
        \] # Closing bracket for second level of balanced square brackets
      )*
    )
\] # Match closing square bracket
'''

# symbol regular expression string
symbol = r'[a-zA-Z]\w*'

# integer regular expression string
integer = r'[-+]?[0-9]+'

# domain pair ( something, somethingElse) regular expression string
domainPair = r'\(\s*(\S+),\s*(\S+)\s*\)'

def escapeStringForRegularExpression(s):
  s = s.replace("\\", "\\\\")   # Escape single backslashes
  s = s.replace(".", "\\.")     # Escape the 'dot'
  s = s.replace("^", "\\^")     # Escape the caret
  s = s.replace("*", "\\*")
  s = s.replace("?", "\\?")
  s = s.replace("{", "\\{")
  s = s.replace("}", "\\}")
  s = s.replace("(", "\\(")
  s = s.replace(")", "\\)")
  s = s.replace("[", "\\[")
  s = s.replace("]", "\\]")
  return s

  