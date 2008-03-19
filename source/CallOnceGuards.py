#!/usr/bin/env python
# encoding: utf-8
"""
CallOnceGuards.py

Created by Graham Dennis on 2007-12-14.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from functools import wraps
from xpdeint._ScriptElement import _ScriptElement


def callOnceGuard(f):
  """Function decorator to prevent a function being called more than once."""
  @wraps(f)
  def wrapper(*args, **KWs):
    # If the function object isn't in the guard set, then add it and run the function
    if not f in _ScriptElement._callOnceGuards:
      _ScriptElement._callOnceGuards.add(f)
      return f(*args, **KWs)
    else:
      return ''
  
  return wrapper


def callOncePerInstanceGuard(f):
  """Function decorator to prevent a function being called more than once for each instance."""
  @wraps(f)
  def wrapper(self, *args, **KWs):
    # If the guard name isn't in the guard set for this instance, then add it and run the function
    if not f in _ScriptElement._callOncePerInstanceGuards[self]:
      _ScriptElement._callOncePerInstanceGuards[self].add(f)
      return f(self, *args, **KWs)
    else:
      return ''
  
  return wrapper
