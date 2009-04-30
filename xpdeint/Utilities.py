#!/usr/bin/env python
# encoding: utf-8
"""
Utilities.py

Created by Graham Dennis on 2008-09-15.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ParserException import ParserException
import re

class lazy_property(object):
  """
  A data descriptor that provides a default value for the attribute
  represented via a user-defined function, and this function is evaluated
  at most once with the result cached. Additionally, the property can be
  overridden.
  """
  
  def __init__(self, fget, doc=None):
    self.fget = fget
    self.__doc__ = doc
    if not self.__doc__:
      self.__doc__ = fget.__doc__
    self.__name__ = fget.__name__
  
  def __get__(self, obj, objtype=None):
    if obj is None:
      return self
    if self.fget is None:
      raise AttributeError, "unreadable attribute"
    result = obj.__dict__[self.__name__] = self.fget(obj)
    return result
  

def valueForKeyPath(base, keyPath):
  """
  Return the value for a dotted-name lookup of `keyPath` anchored at `base`.

  This is similar to the KVC methods in Objective-C, however its use is appropriate in Python.
  Evaluating the `keyPath` 'foo.bar.baz' returns the object that would be returned by evaluating
  the string (in Python) base.foo.bar.baz
  """
  attrNames = keyPath.split('.')
  try:
    currentObject = base
    for attrName in attrNames:
      if isinstance(currentObject, dict):
        # Access via dictionary key
        currentObject = currentObject[attrName]
      else:
        # Access attribute
        currentObject = getattr(currentObject, attrName)
  except Exception, err:
    baseRep = repr(base)
    print >> sys.stderr, "Hit exception trying to get keyPath '%(keyPath)s' on object %(baseRep)s." % locals()
    raise
  return currentObject

def setValueForKeyPath(base, value, keyPath):
  """Set the value of the result of the dotted-name lookup of `keyPath` anchored at `base` to `value`."""
  attrNames = keyPath.split('.')
  lastAttrName = attrNames.pop()
  currentObject = base
  try:
    for attrName in attrNames:
      currentObject = getattr(currentObject, attrName)
    if isinstance(currentObject, dict):
      # Set dictionary entry
      currentObject[lastAttrName] = value
    else:
      # Set attribute
      setattr(currentObject, lastAttrName, value)
  except Exception, err:
    baseRep = repr(base)
    print >> sys.stderr, "Hit exception trying to set keyPath '%(keyPath)s' on object %(baseRep)s." % locals()
    raise


def greatestCommonFactor(num):
    t_val = num[0]
    for cnt in range(len(num)-1):
        num1 = t_val
        num2 = num[cnt+1]
        if num1 < num2:
            num1,num2=num2,num1
        while num1 - num2:
            num3 = num1 - num2
            num1 = max(num2,num3)
            num2 = min(num2,num3)
        t_val = num1
    return t_val

def leastCommonMultiple(num):
    if len(num) == 0:
        return 1
    t_val = num[0]
    for cnt in range(len(num)-1):
        num1 = t_val
        num2 = num[cnt+1]
        tmp = greatestCommonFactor([num1,num2])
        t_val = tmp * num1/tmp * num2/tmp
    return t_val

def leopardWebKitHack():
    """
    Hack for Mac OS X Leopard and above so that it doesn't import
    the web rendering framework WebKit when Cheetah tries to import
    the Python web application framework WebKit.
    """
    import sys
    if sys.platform == 'darwin' and not 'WebKit' in sys.modules:
        module = type(sys)
        sys.modules['WebKit'] = module('WebKit')

protectedNamesSet = set("""
gamma nan ceil floor trunc round remainder abs sqrt hypot
exp log pow cos sin tan cosh sinh tanh acos asin atan
j0 j1 jn y0 y1 yn erf real complex Re Im mod2 integer mod
""".split())

def symbolsInString(string, xmlElement = None):
    wordRegex = re.compile(r'\b\w+\b')
    symbolRegex = re.compile(r'[a-zA-Z]\w*')
    words = wordRegex.findall(string)
    for word in words:
        if not symbolRegex.match(word):
            raise ParserException(
                xmlElement,
                "'%(word)s' is not a valid name. All names must start with a letter, "
                "after that letters, numbers and underscores ('_') may be used." % locals()
            )
        if word in protectedNamesSet:
            raise ParserException(
                xmlElement,
                "'%(word)s' cannot be used as a name because it conflicts with an internal function or variable of the same name. "
                "Choose another name." % locals()
            )
    return words

def symbolInString(string, xmlElement = None):
    words = symbolsInString(string, xmlElement)
    if len(words) > 1:
        raise ParserException(
            xmlElement,
            "Only one name was expected at this point. The problem was with the string '%(string)s'" % locals()
        )
    if words:
        return words[0]
    else:
        return None
    

