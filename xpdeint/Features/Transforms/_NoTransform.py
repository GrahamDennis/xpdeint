#!/usr/bin/env python
# encoding: utf-8
"""
_NoTransform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
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
      name = name, type = type, lattice = lattice,
      _minimum = minimum, _maximum = maximum, _stepSize = stepSize, parent = dim,
      tag = self.dimRepTag, reductionMethod = UniformDimensionRepresentation.ReductionMethod.fixedRange,
      **self.argumentsToTemplateConstructors
    )
    dim.addRepresentation(rep)
    return dim
  

