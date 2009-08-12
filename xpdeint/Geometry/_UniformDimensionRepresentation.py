#!/usr/bin/env python
# encoding: utf-8
"""
_UniformDimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation

class _UniformDimensionRepresentation(DimensionRepresentation):
  instanceAttributes = ['_minimum',  '_maximum', '_stepSize']
  
  @property
  def stepSizeString(self):
    if self._stepSize:
      return self._stepSize
    else:
      return '((%(maximum)s - %(minimum)s)/%(globalLattice)s)' % dict(
        minimum = self.minimum,
        maximum = self.maximum,
        globalLattice = self.globalLattice
      )
  
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
  
  def nonlocalAccessIndexFromStringForFieldInBasis(self, accessString, field, basis):
    result = super(_UniformDimensionRepresentation, self).nonlocalAccessIndexFromStringForFieldInBasis(accessString, field, basis)
    if result: return result
    # We only support non-local access for integer-valued dimensions
    if not self.type == 'long':
      return
    minimum = self.minimum
    if self.hasLocalOffset:
      localOffsetString = ' - ' + self.localOffset
    else: localOffsetString = ''
    return '(%(accessString)s) - %(minimum)s%(localOffsetString)s' % locals()
  

