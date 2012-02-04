#!/usr/bin/env python
# encoding: utf-8
"""
_NonUniformDimensionRepresentation.py

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
  
  instanceAttributes = ['stepSizeArray']
  instanceDefaults = dict(
    stepSizeArray = False
  )
  
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
  

