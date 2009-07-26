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

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.SplitUniformDimensionRepresentation import SplitUniformDimensionRepresentation
from xpdeint.Geometry.NonUniformDimensionRepresentation import NonUniformDimensionRepresentation

from xpdeint.Utilities import permutations, combinations
from xpdeint.ParserException import ParserException

import operator

class _MMT (_Transform):
  transformName = 'MMT'
  
  coordinateSpaceTag = DimensionRepresentation.registerTag('MMT coordinate space')
  spectralSpaceTag = DimensionRepresentation.registerTag('MMT spectral space')
  
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
        except ValueError:
          raise ParserException(xmlElement, "Cannot understand '%s' as a meaningful order. "
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
                                                 tag = self.coordinateSpaceTag,
                                                 **self.argumentsToTemplateConstructors)
      xspace._maximum = maximum
      
      # Spectral space representation
      kspace = NonUniformDimensionRepresentation(name = 'k' + name, type = type, lattice = spectralLattice,
                                                 stepSizeArray = True, parent = dim,
                                                 tag = self.spectralSpaceTag,
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
        raise ParserException(xmlElement, "For 'hermite-gauss' transformed dimensions, use the 'length_scale' attribute "
                                          "instead of 'domain'.")
      
      # Real space representation
      xspace = NonUniformDimensionRepresentation(name = name, type = type, lattice = lattice,
                                                 stepSizeArray = True, parent = dim,
                                                 tag = self.coordinateSpaceTag,
                                                 **self.argumentsToTemplateConstructors)
      xspace._maximum = maximum
      # Spectral space representation
      kspace = UniformDimensionRepresentation(name = 'n' + name, type = 'long', lattice = spectralLattice,
                                              minimum = '0', maximum = spectralLattice, stepSize = '1',
                                              parent = dim, tag = self.spectralSpaceTag,
                                              **self.argumentsToTemplateConstructors)
    dim.addRepresentation(xspace)
    dim.addRepresentation(kspace)
    return dim
  
  def potentialTransforms(self):
    results = []
    geometry = self.getVar('geometry')
    # Sort dimension names based on their ordering in the geometry.
    sortedDimNames = [(geometry.indexOfDimensionName(dimName), dimName) for dimName in self.basisMap]
    sortedDimNames.sort()
    sortedDimNames = [o[1] for o in sortedDimNames]
    # Step one: Create all transforms just for each dimension individually
    # These transforms require an additional copy either at the start or end as there is no
    # in-place matrix multiply.
    for dimName in sortedDimNames:
      dimReps = geometry.dimensionWithName(dimName).representations
      for oldDimRep, newDimRep in permutations(dimReps, dimReps):
        if oldDimRep == newDimRep: continue
        results.append(dict(oldBasis=oldDimRep.name,
                            newBasis=newDimRep.name,
                            cost=oldDimRep.lattice * newDimRep.lattice))
    
    # Step two: Create 'optimised' transforms. These transform two dimensions at a time. This
    # is more optimal as we don't have to have an additional copy as we can perform the first multiply
    # into the temporary array, and the second back into the original storage.
    
    # Consider all combinations of two dimensions
    for dimNames in combinations(2, sortedDimNames):
      dimReps = [geometry.dimensionWithName(dimName).representations for dimName in dimNames]
      # Loop over all possible transforms between these two dimensions
      for oldReps in permutations(*dimReps):
        for newReps in permutations(*dimReps):
          # Only consider the transforms in which every dimension has something change.
          if any([old == new for old, new in zip(oldReps, newReps)]): continue
          transform = {}
          transform['oldDimRep'] = tuple([dimRep.name for dimRep in oldReps])
          transform['newDimRep'] = tuple([dimRep.name for dimRep in newReps])
          # The inherent cost of the multiply
          costs = [oldDimRep.lattice * newDimRep.lattice for oldDimRep, newDimRep in zip(oldReps, newReps)]
          # There is a multiplier due to the number of these matrix multiplies we need
          costMultipliers = [min(oldDimRep.lattice, newDimRep.lattice) for oldDimRep, newDimRep in zip(oldReps, newReps)]
          # The cost for each transform should be multiplied by the smallest size of each other dimension (due to ordering)
          for idx, cost in enumerate(costs):
            costs[idx] *= reduce(operator.mul, costMultipliers[0:idx] + costMultipliers[idx+1:], 1)
          transform['cost'] = reduce(operator.add, costs)
          results.append(transform)
    return results

