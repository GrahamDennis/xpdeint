#!/usr/bin/env python
# encoding: utf-8
"""
Utilities.py

Created by Graham Dennis on 2008-09-15.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

class lazyproperty(object):
  """
  A data descriptor that provides a default value for the attribute
  represented via a user-defined function, and once evaluated, this
  property is evaluated only once. Additionally, the property can be
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
  


