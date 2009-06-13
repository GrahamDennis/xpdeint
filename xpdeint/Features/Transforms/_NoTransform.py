#!/usr/bin/env python
# encoding: utf-8
"""
_NoTransform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms._Transform import _Transform

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation

class _NoTransform (_Transform):
  transformName = 'NoTransform'
  
  dimRepTag = DimensionRepresentation.registerTag('No transform')
  
  def __init__(self, *args, **KWs):
    _Transform.__init__(self, *args, **KWs)
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   type = 'real', spectralLattice = None, xmlElement = None):
    assert transformName == 'none'
    dim = super(_NoTransform, self).newDimension(name, lattice, minimum, maximum,
                                                 parent, transformName, aliases,
                                                 type, xmlElement)
    if type == 'long':
      stepSize = '1'
    else:
      stepSize = None
    rep = UniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                         minimum = minimum, maximum = maximum, stepSize = stepSize, parent = dim,
                                         tag = self.dimRepTag,
                                         **self.argumentsToTemplateConstructors)
    dim.addRepresentation(rep)
    return dim
  
  def canTransformVectorInDimension(self, vector, dim):
    return False
  

