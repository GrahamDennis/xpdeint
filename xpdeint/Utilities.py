#!/usr/bin/env python
# encoding: utf-8
"""
Utilities.py

Created by Graham Dennis on 2008-09-15.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from weakref import WeakKeyDictionary

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

