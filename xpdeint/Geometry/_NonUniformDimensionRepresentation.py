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
  """
  This class represents a dimension with non-uniform spacing. This corresponds
  to two main possibilities.
  
  The first is the propagation dimension where each point in this dimension
  corresponds to a time at which sampling occurred. This isn't necessarily
  uniform.
  
  The second is a Gauss-Lobotto grid for a transverse dimension in the problem.
  In this case, the points will not be equally spaced in order to optimise
  integration across the dimension. Also, the 'step size' variable in this case
  corresponds to the Gauss-Lobotto weight for each grid point and is not directly
  related to the separation of two neighbouring grid points. This is perfectly
  sensible as the step size is only used as a weight when integrating across
  dimensions, which is exactly where the weight should be used.
  """
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['stepSizeArray', 'maximum'], KWs)
    DimensionRepresentation.__init__(self, **KWs)
    
    self.stepSizeArray = localKWs.get('stepSizeArray', False)
    self._maximum = localKWs.get('maximum')
  
  def __eq__(self, other):
    try:
      return (DimensionRepresentation.__eq__(self, other) and
              self.stepSizeArray == other.stepSizeArray and
              self._maximum == other._maximum)
    except AttributeError:
      return NotImplemented
  
  def _newInstanceDict(self):
    result = DimensionRepresentation._newInstanceDict(self)
    result.update({'stepSizeArray': self.stepSizeArray, 'maximum': self._maximum})
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
  

