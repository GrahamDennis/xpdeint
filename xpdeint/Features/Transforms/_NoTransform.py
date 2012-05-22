#!/usr/bin/env python
# encoding: utf-8
"""
_NoTransform.py

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

from xpdeint.Features.Transforms._Transform import _Transform

from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation

class _NoTransform (_Transform):
  transformName = 'NoTransform'
  
  dimRepTag = UniformDimensionRepresentation.registerTag('No transform', parent = 'coordinate')
  
  def __init__(self, *args, **KWs):
    _Transform.__init__(self, *args, **KWs)
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   type = 'real', spectralLattice = None, volumePrefactor = None,
                   xmlElement = None):
    assert transformName == 'none'
    dim = super(_NoTransform, self).newDimension(name, lattice, minimum, maximum,
                                                 parent, transformName, aliases,
                                                 type, volumePrefactor, xmlElement)
    if type == 'long':
      stepSize = '1'
    else:
      stepSize = None
    rep = UniformDimensionRepresentation(
      name = name, type = type, runtimeLattice = lattice,
      _minimum = minimum, _maximum = maximum, _stepSize = stepSize, parent = dim,
      tag = self.dimRepTag, reductionMethod = UniformDimensionRepresentation.ReductionMethod.fixedRange,
      **self.argumentsToTemplateConstructors
    )
    dim.addRepresentation(rep)
    return dim
  

