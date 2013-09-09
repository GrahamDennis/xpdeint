#!/usr/bin/env python
# encoding: utf-8
"""
_SplitUniformDimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.

Copyright (c) 2008-2012, Graham Dennis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Utilities import lazy_property

class _SplitUniformDimensionRepresentation(DimensionRepresentation):
  instanceAttributes = ['_range']
  
  @lazy_property
  def alternateLoopIndex(self):
    return '_j_' + self.name
  
  def openLoop(self, loopingOrder):
    if loopingOrder == self.LoopingOrder.MemoryOrder:
      return self.openLoopMemoryOrder()
    elif loopingOrder == self.LoopingOrder.StrictlyAscendingOrder:
      assert not self.hasLocalOffset
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
  
  def nonlocalAccessIndexFromStringForFieldInBasis(self, accessString, field, basis):
    result = super(_SplitUniformDimensionRepresentation, self).nonlocalAccessIndexFromStringForFieldInBasis(accessString, field, basis)
    if result: return result
    # We only support access with the negative of the dimension variable. e.g. -kx
    name = self.name
    aliasRepresentations = self.aliasRepresentationsForFieldInBasis(field, basis)
    matchingAliasReps = [dimRep for dimRep in aliasRepresentations if accessString == ('-' + dimRep.name)]
    assert len(matchingAliasReps) <= 1
    if not matchingAliasReps: return
    matchingAliasRep = matchingAliasReps[0]
    
    # We only support the case where the global number of points in the looping dimension and the
    # accessing dimension are the same. i.e. no sub-sampling and non-local access at the same time.
    if not field.hasDimensionName(matchingAliasRep.parent.name): return
    loopDimRep = field.dimensionWithName(matchingAliasRep.parent.name).inBasis(basis)
    if not matchingAliasRep.runtimeLattice == loopDimRep.runtimeLattice: return
    loopingIndex = loopDimRep.loopIndex
    globalLattice = matchingAliasRep.globalLattice
    return '(%(globalLattice)s - %(loopingIndex)s) %% %(globalLattice)s' % locals()
  




