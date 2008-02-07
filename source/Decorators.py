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
  attributeGuardName = ''.join(['_', className, '_', f.__name__, '_callOnceGuard_called'])
  
  setattr(_ScriptElement, attributeGuardName, False)
  
  @wraps(f)
  def wrapper(*args, **KWs):
    if getattr(_ScriptElement, attributeGuardName) == False:
      setattr(_ScriptElement, attributeGuardName, True)
      return f(*args, **KWs)
  
  return wrapper


def callOncePerInstanceGuard(f):
  """Function decorator to prevent a function being called more than once for each instance."""
  className = sys._getframe(1).f_code.co_name
  attributeGuardName = ''.join(['_', className, '_', f.__name__, '_callOnceGuard_called'])
  
  setattr(_ScriptElement, attributeGuardName, False)
  
  @wraps(f)
  def wrapper(self, *args, **KWs):
    if getattr(self, attributeGuardName) == False:
      setattr(self, attributeGuardName, True)
      return f(self, *args, **KWs)
  
  return wrapper
