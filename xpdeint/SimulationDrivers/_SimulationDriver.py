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
    """
    Returns `True` if `dimension` could have a local offset.
    
    This should only be true for dimensions that are distributed with MPI.
    """
    return False
  
  def localOffsetForDimensionInFieldInSpace(self, dimension, field, space):
    return "0"
  
  def localLatticeForDimensionInFieldInSpace(self, dimension, field, space):
    return ''.join(['_', field.name, '_lattice_', self.dimensionNameForSpace(dimension, space)])
  
  def sizeOfFieldInSpace(self, field, space):
    """Return a name of a variable the value of which is the size of `field` in `space`."""
    return '_' + field.name + '_alloc_size'
  
  def sizeOfVector(self, vector):
    return self.sizeOfVectorInSpace(vector, None)
  
  def orderedDimensionsForFieldInSpace(self, field, space):
    """Return a list of the dimensions for field in the order in which they should be looped over"""
    return field.dimensions[:]
  
  
