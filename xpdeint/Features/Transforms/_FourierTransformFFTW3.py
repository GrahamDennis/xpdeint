#!/usr/bin/env python,
# encoding: utf-8
"""
_FourierTransform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms._Transform import _Transform

from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.SplitUniformDimensionRepresentation import SplitUniformDimensionRepresentation

from xpdeint.ParserException import ParserException

class _FourierTransformFFTW3 (_Transform):
  transformName = 'FourierTransform'
  
  def __init__(self, *args, **KWs):
    _Transform.__init__(self, *args, **KWs)
    self.transformNameMap = {}
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   spectralLattice = None,
                   type = 'real', xmlElement = None):
    assert type == 'real'
    assert transformName in ['dft', 'dct', 'dst']
    dim = super(_FourierTransformFFTW3, self).newDimension(name, lattice, minimum, maximum,
                                                           parent, transformName, aliases,
                                                           type, xmlElement)
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
    result = super(_FourierTransformFFTW3, self).canTransformVectorInDimension(vector, dim)
    if result:
      transformName = self.transformNameMap[dim.name]
      # We can only transform complex vectors with dft.
      # dct/dst can manage both complex and double
      if transformName == 'dft' and not vector.type == 'complex':
        result = False
    
    return result
  
  def r2rKindForDimensionAndDirection(self, dim, direction):
    transformName = self.transformNameMap[dim.name]
    return {'dct': {'forward': 'FFTW_REDFT10', 'backward': 'FFTW_REDFT01'},
            'dst': {'forward': 'FFTW_RODFT10', 'backward': 'FFTW_RODFT01'}}[transformName][direction]
  
  def initialiseForMPIWithDimensions(self, dimensions):
    # We can only upgrade to MPI support if both the first and second dimensions
    # are 'dft' or 'r2r' transforms. In the future, this restriction can be lifted
    if len(dimensions) < 2:
      raise ParserException(self._driver.xmlElement,
                            "There must be at least two dimensions to use the 'distributed-mpi' with the '%s' transform." % self.transformName[dimensions[0].name])
    if not (dimensions[0].transform == self and dimensions[1].transform == self) \
       or ((self.transformNameMap[dimensions[0].name] == 'dft') ^ (self.transformNameMap[dimensions[1].name] == 'dft')) \
       or ((self.transformNameMap[dimensions[0].name] in ['dct', 'dst']) ^ (self.transformNameMap[dimensions[1].name] in ['dct', 'dst'])):
      raise ParserException(self._driver.xmlElement,
                            "To use the 'distributed-mpi' driver with the 'dft', 'dct' or 'dst' transforms, both the first and second dimensions\n"
                            "must use one of these transforms with the additional restriction that if the 'dft' transform is used for one dimension\n"
                            "it must be used for the other.")
    super(_FourierTransformFFTW3, self).initialiseForMPIWithDimensions(dimensions)
  

