#!/usr/bin/env python
# encoding: utf-8
"""
RegularExpressionStrings.py

Created by Graham Dennis on 2008-02-20.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""
import re

threeLevelsMatchedSquareBrackets = r'''
\[ # Match initial opening square bracket

    # Now make a group for the 'innerContents' of the square brackets
    (
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

# C expression that includes up to two levels of nested parentheses
cExpression = r'''
(?: # Non-capturing group
  # A C expression is any character not a comma, semicolon, parentheses or square brackets
  [^,;()\[\]]
  | # ... or nested parentheses
  (?:
    \( # Which begins with an opening parenthesis
      (?:
        # Contains either a non-parenthesis character
        [^()]
        | # ... or balanced parentheses
        \( # Second level of opening parentheses
          [^()]*
        \) # Second level of closing parentheses
      )*
    \) # and ends with a closing parenthesis
  )*
  | # ... or nested square brackets
  (?:
    \[ # First level of opening square brackets
      (?:
        [^\[\]]
        |
        \[ # Second level of opening square brackets
          [^\[\]]*
        \] # Second level of closing square brackets
      )*
    \] # First level of closing square brackets
  )*
)*
'''


# symbol regular expression string
symbol = r'[a-zA-Z]\w*'

# integer regular expression string
integer = r'[-+]?[0-9]+'

# domain pair ( something, somethingElse) regular expression string
domainPair = r'\(\s*(\S+),\s*(\S+)\s*\)'

def componentWithIntegerValuedDimensions(components):
  """
  Return a regular expression string used for matching components followed by integer-valued dimensions specifiers.
  
  For example, this regular expression should match:
  ``phi[j, k, 2*7 - m][n*n, blah]``
  if 'phi' is an element of `components`.
  """
  
  legalComponentNames = set(components)
  
  # The regular expression is of the form:
  # (?P<componentName>component1|component2)(?P<integerValuedDimensions>\[balancedString\](?:\[balancedString\])?)?
  # So the component could be followed by one or two pairs of square brackets,
  # and this is not checked against the dimensions of the field that the component belongs to.
  
  return '(?P<componentName>' + '|'.join(legalComponentNames) + ')' \
            + '(?P<integerValuedDimensions>' + threeLevelsMatchedSquareBrackets \
              + '(?:' + threeLevelsMatchedSquareBrackets + ')?)?'


def integerValuedDimensionsForComponentInField(componentName, field):
  """
  Return a regular expression string used for extracting the arguments to the integer-valued dimensions
  for a given component in a known field.
  """
  
  integerValuedDimensionsRegexString = ''
  integerValuedDimensions = field.integerValuedDimensions
  integerValuedDimensionNames = []
  
  for listOfIntegerValuedDimensions in integerValuedDimensions:
    integerValuedDimensionsRegexGroups = ['(?P<' + dim.name + '>' + cExpression + ')' for dim in listOfIntegerValuedDimensions]
    integerValuedDimensionsRegexString += r'\[' + ','.join(integerValuedDimensionsRegexGroups) + r'\]'
    integerValuedDimensionNames.extend([dim.name for dim in listOfIntegerValuedDimensions])
  
  # The expression is of the form:
  # componentName(?P<integerValuedDimensions>\[(?P<j>cExpression),(?P<k>cExpression)\])
  # i.e. should match anything of the form
  # componentName[ j*k + 1, 0 ]
  regexString = componentName + '(?P<integerValuedDimensions>' + integerValuedDimensionsRegexString + ')'
  
  return regexString



def symbolsInString(string):
  """
  Return a list of all symbols in `string`.
  
  A 'symbol' is a C language token.
  It can contain underscores, numbers and upper or lower-case characters,
  except for the first character which must be an upper or lower-case 
  character.
  """
  symbolNameRegex = re.compile(r'\b' + symbol + r'\b')
  results = symbolNameRegex.findall(string)
  return results

def symbolInString(string):
  """
  Return the single symbol in `string`.
  
  If there is more than one symbol in this string (as determined by `symbolsInString`),
  this method will raise a `ValueError` exception.
  """
  results = symbolsInString(string)
  if len(results) > 1:
    raise ValueError('Too many symbols')
  elif len(results) == 0:
    return None
  else:
    return results[0]

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
  
