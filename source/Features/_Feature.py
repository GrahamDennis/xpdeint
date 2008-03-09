#!/usr/bin/env python
# encoding: utf-8
"""
_Feature.py

This contains all the pure-python code for all features

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from .ScriptElement import ScriptElement

class _Feature (ScriptElement):
  def __init__(self, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    
    self.getVar('features')[self.featureName] = self
    self.getVar('scriptElements').append(self)
  
