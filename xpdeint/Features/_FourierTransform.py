#!/usr/bin/env python,
# encoding: utf-8
"""
_FourierTransform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transform import Transform

from xpdeint.Geometry._Dimension import _Dimension
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.SplitUniformDimensionRepresentation import SplitUniformDimensionRepresentation

class _FourierTransform (Transform):
  def __init__(self, *args, **KWs):
    Transform.__init__(self, *args, **KWs)
    
    self.getVar('transforms')['dft'] = self
    self.getVar('transforms')['dct'] = self
    self.getVar('transforms')['dst'] = self
    
    self.transformNameMap = {}
  
  def newDimension(self, name, lattice, minimum, maximum, parent, transformName, type = 'double', indexable = False):
    assert type == 'double'
    assert transformName in ['dft', 'dct', 'dst']
    dim = _Dimension(name = name, transform = self, parent = parent, indexable = indexable,
                     **self.argumentsToTemplateConstructors)
    self.transformNameMap[dim.name] = transformName
    if transformName == 'dft':
      # x-space representation
      xspace = UniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                              minimum = minimum, maximum = maximum, parent = dim,
                                              **self.argumentsToTemplateConstructors)
      # kspace representation
      kspace = SplitUniformDimensionRepresentation(name = 'k' + name, type = type, lattice = lattice,
                                                   range = '%s - %s' % (xspace.maximum, xspace.minimum),
                                                   parent = dim,
                                                   **self.argumentsToTemplateConstructors)
    else:
      # x-space representation
      stepSize = '((double)%(maximum)s - %(minimum)s)/(%(lattice)s)' % locals()
      xspace = UniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                              minimum = None, maximum = None, stepSize = stepSize,
                                              parent = dim, **self.argumentsToTemplateConstructors)
      # Modify the minimum and maximum values to deal with the 0.5*stepSize offset
      xspace._minimum = '%s + 0.5*%s' % (minimum, xspace.stepSize)
      xspace._maximum = '%s + 0.5*%s' % (maximum, xspace.stepSize)
      if transformName == 'dct':
        # kspace representation
        kspace = UniformDimensionRepresentation(name = 'k' + name, type = type, lattice = lattice,
                                                minimum = '0.0', maximum = None,
                                                stepSize = '(M_PI/(%(maximum)s - %(minimum)s))' % locals(),
                                                parent = dim, **self.argumentsToTemplateConstructors)
        kspace._maximum = '%s * %s' % (kspace.stepSize, kspace.globalLattice)
      else:
        kspace = UniformDimensionRepresentation(name = 'k' + name, type = type, lattice = lattice,
                                                minimum = None, maximum = None,
                                                stepSize = '(M_PI/(%(maximum)s - %(minimum)s))' % locals(),
                                                parent = dim, **self.argumentsToTemplateConstructors)
        kspace._minimum = '%s' % kspace.stepSize
        kspace._maximum = '%s * (%s + 1)' % (kspace.stepSize, kspace.globalLattice)
    
    dim.addRepresentation(xspace)
    dim.addRepresentation(kspace)
    return dim
  
  def canTransformVectorInDimension(self, vector, dim):
    result = super(_FourierTransform, self).canTransformVectorInDimension(vector, dim)
    if result:
      transformName = self.transformNameMap[dim.name]
      # We can only transform complex vectors with dft.
      # dct/dst can manage both complex and double
      if transformName == 'dft' and not vector.type == 'complex':
        result = False
    
    return result
    
