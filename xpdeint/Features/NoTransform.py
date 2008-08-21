#!/usr/bin/env python
# encoding: utf-8
"""
NoTransform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transform import Transform

from xpdeint.Geometry._Dimension import _Dimension
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation

class NoTransform (Transform):
  featureName = 'NoTransform'
  
  def __init__(self, *args, **KWs):
    Transform.__init__(self, *args, **KWs)
    
    self.getVar('transforms')['none'] = self
  
  def newDimension(self, name, lattice, minimum, maximum, parent, transformName, type = 'double', indexable = False):
    assert transformName == 'none'
    dim = _Dimension(name = name, transform = self, parent = parent, indexable = indexable, **self.argumentsToTemplateConstructors)
    if type == 'long':
      stepSize = '1'
    else:
      stepSize = None
    rep = UniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                         minimum = minimum, maximum = maximum, stepSize = stepSize, parent = dim,
                                         **self.argumentsToTemplateConstructors)
    dim.addRepresentation(rep)
    return dim
  
  def canTransformVectorInDimension(self, vector, dim):
    return False
