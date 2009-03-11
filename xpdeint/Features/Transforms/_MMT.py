#!/usr/bin/env python,
# encoding: utf-8
"""
_MMT.py

Created by Graham Dennis on 2008-12-12.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms._Transform import _Transform

from xpdeint.Features.Transforms.BesselBasis import BesselBasis
from xpdeint.Features.Transforms.SphericalBesselBasis import SphericalBesselBasis
from xpdeint.Features.Transforms.HermiteGaussEPBasis import HermiteGaussEPBasis

from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.SplitUniformDimensionRepresentation import SplitUniformDimensionRepresentation
from xpdeint.Geometry.NonUniformDimensionRepresentation import NonUniformDimensionRepresentation

from xpdeint.ParserException import ParserException

class _MMT (_Transform):
  transformName = 'MMT'
  
  def __init__(self, *args, **KWs):
    _Transform.__init__(self, *args, **KWs)
    self.basisMap = {}
  
  @property
  def children(self):
    children = super(_MMT, self).children
    children.extend(self.basisMap.values())
    return children
  
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   spectralLattice = None,
                   type = 'real', xmlElement = None):
    assert type == 'real'
    assert transformName in ['bessel', 'spherical-bessel', 'hermite-gauss']
    if not spectralLattice:
      spectralLattice = lattice
    dim = super(_MMT, self).newDimension(name, max(lattice, spectralLattice), minimum, maximum,
                                         parent, transformName, aliases, 
                                         type, xmlElement)
    self.basisMap[dim.name] = transformName # Needs to be constructed basis here
    
    if transformName == 'chby':
      # Chebyshev polynomials
      self.basisMap[dim.name] = blah # Instantiate ChebyschevBasis
      # x-space representation
      xspace = NonUniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                                 parent = dim,
                                                 **self.argumentsToTemplateConstructors)
      xspace._minimum = minimum
      xspace._maximum = maximum
      # transformed space representation
      kspace = UniformDimensionRepresentation(name = 'n' + name, type = 'long', lattice = lattice,
                                              minimum = '0', maximum = lattice, stepSize = '1',
                                              parent = dim,
                                              **self.argumentsToTemplateConstructors)
    elif transformName in ('bessel', 'spherical-bessel'):
      # Bessel functions
      order = 0
      if xmlElement.hasAttribute('order'):
        features = self.getVar('features')
        orderString = xmlElement.getAttribute('order')
        try:
          order = int(orderString)
        except:
          raise ParserException(xmlElement, "Cannot understand '%s' as a meaningful order.\n"
                                            "Order values must be non-negative integers." \
                                            % xmlElement.getAttribute('order'))
        else:
          if order < 0:
            raise ParserException(xmlElement, "The 'order' attribute for Bessel transforms must be non-negative.")
      besselBasisClass = BesselBasis
      if transformName == 'spherical-bessel':
        besselBasisClass = SphericalBesselBasis
      otherBesselBases = [basis for basis in self.basisMap.values() if isinstance(basis, besselBasisClass) and basis.order == order]
      if otherBesselBases:
        # Use other basis instead of creating another
        self.basisMap[dim.name] = otherBesselBases[0]
      else:
        basis = besselBasisClass(parent = self, **self.argumentsToTemplateConstructors)
        basis.order = order
        self.basisMap[dim.name] = basis
      
      if not float(minimum) == 0.0:
        raise ParserException(xmlElement, "The domain for Bessel transform dimensions must begin at 0.")
      
      # Real space representation
      xspace = NonUniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                                 stepSizeArray = True, parent = dim,
                                                 **self.argumentsToTemplateConstructors)
      xspace._maximum = maximum
      
      # Spectral space representation
      kspace = NonUniformDimensionRepresentation(name = 'k' + name, type = type, lattice = spectralLattice,
                                                 stepSizeArray = True, parent = dim,
                                                 **self.argumentsToTemplateConstructors)
      kspace._maximum = maximum
    elif transformName == 'hermite-gauss':
      # Hermite-gauss basis (harmonic oscillator)
      otherHGBases = [basis for basis in self.basisMap.values() if isinstance(basis, HermiteGaussEPBasis)]
      if otherHGBases:
        # Use other basis instead of creating another
        self.basisMap[dim.name] = otherHGBases[0]
      else:
        basis = HermiteGaussEPBasis(parent = self, **self.argumentsToTemplateConstructors)
        self.basisMap[dim.name] = basis
      
      if not float(minimum) == 0.0:
        raise ParserException(xmlElement, "For 'hermite-gauss' transformed dimensions, use the 'length_scale' attribute\n"
                                          "instead of 'domain'.\n")
      
      # Real space representation
      xspace = NonUniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                                 stepSizeArray = True, parent = dim,
                                                 **self.argumentsToTemplateConstructors)
      xspace._maximum = maximum
      # Spectral space representation
      kspace = UniformDimensionRepresentation(name = 'n' + name, type = 'long', lattice = spectralLattice,
                                              minimum = '0', maximum = spectralLattice, stepSize = '1',
                                              parent = dim,
                                              **self.argumentsToTemplateConstructors)
    dim.addRepresentation(xspace)
    dim.addRepresentation(kspace)
    return dim
  
  

