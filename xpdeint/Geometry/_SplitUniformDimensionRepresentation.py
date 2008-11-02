#!/usr/bin/env python
# encoding: utf-8
"""
_SplitUniformDimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Utilities import lazy_property

class _SplitUniformDimensionRepresentation(DimensionRepresentation):
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['range'], KWs)
    DimensionRepresentation.__init__(self, **KWs)
    
    self._range = localKWs['range']
  
  def __eq__(self, other):
    try:
      return (DimensionRepresentation.__eq__(self, other) and
              self._range == other._range)
    except AttributeError:
      return NotImplemented
  
  def _newInstanceDict(self):
    result = DimensionRepresentation._newInstanceDict(self)
    result.update({'range': self._range})
    return result
  
  @lazy_property
  def alternateLoopIndex(self):
    return '_j_' + self.name
  
  def openLoop(self, loopingOrder):
    if loopingOrder == self.LoopingOrder.MemoryOrder:
      return self.openLoopMemoryOrder()
    elif loopingOrder == self.LoopingOrder.StrictlyAscendingOrder:
      return self.openLoopAscending()
    else:
      raise NotImplemented
  
  def closeLoop(self, loopingOrder):
    if loopingOrder == self.LoopingOrder.MemoryOrder:
      return self.closeLoopMemoryOrder()
    elif loopingOrder == self.LoopingOrder.StrictlyAscendingOrder:
      return self.closeLoopAscending()
    else:
      raise NotImplemented
  


