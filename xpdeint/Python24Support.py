#!/usr/bin/env python
# encoding: utf-8
"""
Python24Support.py

Created by Graham Dennis on 2008-07-16.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.

This module adds missing features from python 2.4 that are
available in later versions which xpdeint depends on.
"""

import sys
module = type(sys)

try:
  import functools
except ImportError, err:
  functools = module('functools')
  sys.modules['functools'] = functools
  # Functools function decorator
  def wraps(f):
    def decorator(fn):
      return fn
    return decorator
  
  functools.wraps = wraps
  

try:
  all = sys.modules['__builtin__'].all
except AttributeError, err:
  def all(iter):
    for element in iter:
      if not element:
        return False
    return True
  sys.modules['__builtin__'].all = all

try:
  any = sys.modules['__builtin__'].any
except AttributeError, err:
  def any(iter):
    for element in iter:
      if element:
        return True
    return False
  sys.modules['__builtin__'].any = any
  

try:
  import hashlib
except ImportError, err:
  hashlib = module('hashlib')
  sys.modules['hashlib'] = hashlib
  from sha import new as sha1
  hashlib.sha1 = sha1

