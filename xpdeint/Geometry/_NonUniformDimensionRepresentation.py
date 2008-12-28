#!/usr/bin/env python
# encoding: utf-8
"""
_NonUniformDimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Utilities import lazy_property

class _NonUniformDimensionRepresentation(DimensionRepresentation):
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['stepSizeArray'], KWs)
    DimensionRepresentation.__init__(self, **KWs)
    
    self.stepSizeArray = localKWs.get('stepSizeArray', False)
  
  def __eq__(self, other):
    try:
      return (DimensionRepresentation.__eq__(self, other) and
              self.stepSizeArray == other.stepSizeArray)
    except AttributeError:
      return NotImplemented
  
  def _newInstanceDict(self):
    result = DimensionRepresentation._newInstanceDict(self)
    result.update({'stepSizeArray': self.stepSizeArray})
    return result
  
  @lazy_property
  def index(self):
    return self.prefix + '_index_' + self.name
  
  @lazy_property
  def arrayName(self):
    return self.prefix + '_' + self.name
  
  @lazy_property
  def stepSizeArrayName(self):
    return self.prefix + '_d' + self.name + '_array'
  
  @lazy_property
  def stepSize(self):
    if self.stepSizeArray:
      # We can do this because the step size is only defined inside a loop as the 
      # step size depends on position.
      return 'd' + self.name
    else:
      return super(_NonUniformDimensionRepresentation, self).stepSize
  
  def openLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.openLoopAscending()
    else:
      raise NotImplemented
  
  def closeLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.closeLoopAscending()
    else:
      raise NotImplemented
  

