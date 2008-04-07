#!/usr/bin/env python
# encoding: utf-8
"""
_SimulationDriver.py

Created by Graham Dennis on 2008-02-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

class _SimulationDriver (ScriptElement):
  logLevelsBeingLogged = "_ALL_LOG_LEVELS"
  
  def __init__(self, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    
    self.getVar('features')['Driver'] = self
    # Put ourselves at the start after the simulation element
    self.getVar('scriptElements').insert(1, self)
    self.distributedDimensionNames = []
  
  def mayHaveLocalOffsetForDimensionInFieldInSpace(self, dimension, field, space):
    return False
  
  def localOffsetForDimensionInFieldInSpace(self, dimension, field, space):
    return "0"
  
  def localLatticeForDimensionInFieldInSpace(self, dimension, field, space):
    return ''.join(['_', field.name, '_lattice_', self.dimensionNameForSpace(dimension, space)])
  
