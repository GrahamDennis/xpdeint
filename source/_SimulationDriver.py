#!/usr/bin/env python
# encoding: utf-8
"""
_SimulationDriver.py

Created by Graham Dennis on 2008-02-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from _ScriptElement import _ScriptElement

class _SimulationDriver (_ScriptElement):
  logLevelsBeingLogged = "_ALL_LOG_LEVELS"
  
  def __init__(self, *args, **KWs):
    _ScriptElement.__init__(self, *args, **KWs)
    
    self.getVar('features')['Driver'] = self
    # Put ourselves at the start after the simulation element
    self.getVar('scriptElements').insert(1, self)
  
