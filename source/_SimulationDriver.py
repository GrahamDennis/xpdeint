#!/usr/bin/env python
# encoding: utf-8
"""
_SimulationDriver.py

Created by Graham Dennis on 2008-02-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from TopLevelSequenceElement import TopLevelSequenceElement

class _SimulationDriver (TopLevelSequenceElement):
  logLevelsBeingLogged = "_ALL_LOG_LEVELS"
  
  def __init__(self, *args, **KWs):
    TopLevelSequenceElement.__init__(self, *args, **KWs)
    
    self.getVar('features')['Driver'] = self
  
