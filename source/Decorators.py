#!/usr/bin/env python
# encoding: utf-8
"""
Decorators.py

Created by Graham Dennis on 2007-12-14.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from functools import wraps
import sys
from _ScriptElement import _ScriptElement


def callOncePerClassGuard(f):
  """Function decorator to prevent a function being called more than once (per class)."""
  className = sys._getframe(1).f_code.co_name
  guardName = ''.join(['_', className, '_', f.__name__, '_callOnceGuard_called'])
  
  @wraps(f)
  def wrapper(*args, **KWs):
    # If the guard name isn't in the guard set, then add it and run the function
    if not guardName in _ScriptElement._callOncePerClassGuards:
      _ScriptElement._callOncePerClassGuards.add(guardName)
      return f(*args, **KWs)
    else:
      return ''
  
  return wrapper


def callOncePerInstanceGuard(f):
  """Function decorator to prevent a function being called more than once for each instance."""
  className = sys._getframe(1).f_code.co_name
  guardName = ''.join(['_', className, '_', f.__name__, '_callOnceGuard_called'])
  
  @wraps(f)
  def wrapper(self, *args, **KWs):
    # If the guard name isn't in the guard set for this instance, then add it and run the function
    if not guardName in _ScriptElement._callOncePerInstanceGuards[self]:
      _ScriptElement._callOncePerInstanceGuards[self].add(guardName)
      return f(self, *args, **KWs)
    else:
      return ''
  
  return wrapper
