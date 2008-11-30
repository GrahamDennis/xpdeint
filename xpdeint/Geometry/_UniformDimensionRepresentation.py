#!/usr/bin/env python
# encoding: utf-8
"""
_UniformDimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation

class _UniformDimensionRepresentation(DimensionRepresentation):
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['minimum', 'maximum', 'stepSize'], KWs)
    DimensionRepresentation.__init__(self, **KWs)
    
    self._minimum = localKWs['minimum']
    self._maximum = localKWs['maximum']
    self._stepSize = localKWs.get('stepSize', None)
    
  
  def __eq__(self, other):
    try:
      return (DimensionRepresentation.__eq__(self, other) and
              self._minimum == other._minimum and
              self._maximum == other._maximum and
              self._stepSize == other._stepSize)
    except AttributeError:
      return NotImplemented
  
  def _newInstanceDict(self):
    result = DimensionRepresentation._newInstanceDict(self)
    result.update({'minimum': self._minimum, 'maximum': self._maximum, 'stepSize': self._stepSize})
    return result
  
  @property
  def stepSizeString(self):
    if self._stepSize:
      return self._stepSize
    else:
      d = {'minimum': self.minimum, 'maximum': self.maximum, 'globalLattice': self.globalLattice}
      return '((%(maximum)s - %(minimum)s)/%(globalLattice)s)' % d
  
  
  def openLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.openLoopAscending()
    elif loopingOrder == self.LoopingOrder.StrictlyDescendingOrder:
      return self.openLoopDescending()
    else:
      raise NotImplemented
  
  def closeLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.closeLoopAscending()
    elif loopingOrder == self.LoopingOrder.StrictlyDescendingOrder:
      return self.closeLoopDescending()
    else:
      raise NotImplemented
  
  def nonlocalAccessIndexFromStringForFieldInSpace(self, accessString, field, space):
    result = super(_UniformDimensionRepresentation, self).nonlocalAccessIndexFromStringForFieldInSpace(accessString, field, space)
    if result: return result
    # We only support non-local access for integer-valued dimensions
    if not self.type == 'long':
      return
    minimum = self.minimum
    if self.hasLocalOffset:
      localOffsetString = ' - ' + self.localOffset
    else: localOffsetString = ''
    return '(%(accessString)s) - %(minimum)s%(localOffsetString)s' % locals()
  

