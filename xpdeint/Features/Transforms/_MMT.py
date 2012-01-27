#!/usr/bin/env python,
# encoding: utf-8
"""
_MMT.py

Created by Graham Dennis on 2008-12-12.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms._Transform import _Transform

from xpdeint.Features.Transforms.BesselBasis import BesselBasis
from xpdeint.Features.Transforms.HermiteGaussEPBasis import HermiteGaussEPBasis
from xpdeint.Features.Transforms.HermiteGaussFourierEPBasis import HermiteGaussFourierEPBasis

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.BesselDimensionRepresentation import BesselDimensionRepresentation
from xpdeint.Geometry.SphericalBesselDimensionRepresentation import SphericalBesselDimensionRepresentation
from xpdeint.Geometry.HermiteGaussDimensionRepresentation import HermiteGaussDimensionRepresentation

from xpdeint.ParserException import ParserException

import operator

# We don't directly import mpmath so that mpmath isn't a requirement for xpdeint
# unless you use MMT's.
mpmath = None

# Again, don't directly import numpy
numpy = None

def require_mpmath():
  global mpmath
  if not mpmath:
    import mpmath
    if not hasattr(mpmath, 'besselj'):
      mpmath.besselj = mpmath.jn
    mpmath.mp.prec = 64
    

def require_numpy():
  global numpy
  if not numpy:
    import numpy

def normalisedExtremeHermite(n, x):
  """
  Evaluate the normalised 'extreme' Hermite polynomial H_n(x) exp(-x^2/2)/(sqrt(n! 2^n sqrt(pi))).
  """
  require_numpy()
  assert isinstance(n, int)
  x = numpy.array(x)
  expFactor = numpy.exp(-x*x/(2*n))
  expFactor2 = numpy.exp(-x*x/n)
  hermites = [None, 0.0, numpy.power(numpy.pi, -0.25) * expFactor]
  for j in range(1, n+1):
    hermites[:2] = hermites[1:]
    hermites[2] = x * numpy.sqrt(2./j) * hermites[1] * expFactor \
                  - numpy.sqrt((j-1.)/j) * hermites[0] * expFactor2
  return hermites[2]


def hermiteZeros(n):
  """Return the n zeros of the nth Hermite polynomial H_n(x)."""
  # This method works by constructing a matrix T_n such that |T_n - xI| = H_n(x)
  # where I is the identity matrix. The matrix T_n is tridiagonal and is constructed
  # via the recurrence relationship
  #
  #           b p (x) = (x - a ) p   (x) - b   p   (x)
  #            j j            j   j-1       j-1 j-2
  #
  # The constructed matrix has a_j on the diagonal and sqrt(b_j) on the two neighbouring diagonals.
  #
  # The recurrence relationship for H_n(x) has a_n = 0 and b_n = sqrt(n/2).
  # To improve the accuracy and speed of the calculation of the roots we note that the roots are symmetric
  # about zero and the Hermite functions can be written as
  #
  #                          2
  #            H (x) = J   (x ) for even x, and 
  #             n       n/2
  #
  #                                2
  #            H (x) = x K       (x ) for odd x.
  #             n         (n-1)/2
  #
  # For even n, the recurrence relation for J_n is defined by a_n = 2n - 3/2, b_n = sqrt( n (n - 1/2) ).
  # For odd n, the recurrence relation for K_n is defined by a_n = 2n - 1/2, b_n = sqrt( n (n + 1/2) ).
  
  require_numpy()
  assert isinstance(n, int)
  positiveRoots = n//2
  if (n & 1) == 0:
    # n is even
    a = 2*numpy.arange(1, positiveRoots + 1) - 1.5
    b = numpy.sqrt(numpy.arange(1, positiveRoots) * (numpy.arange(1, positiveRoots) - 0.5))
  else:
    # n is odd
    a = 2*numpy.arange(1, positiveRoots + 1) - 0.5
    b = numpy.sqrt(numpy.arange(1, positiveRoots) * (numpy.arange(1, positiveRoots) + 0.5))
  nproots = numpy.sqrt(numpy.linalg.eigvalsh(numpy.diag(a) + numpy.diag(b, -1)))
  roots = list(nproots)
  # Add the negative roots
  roots.extend(-nproots)
  # if n is odd, add zero as a root
  if (n & 1) == 1: roots.append(0.0)
  roots.sort()
  # Convert back to python float format for storage.
  return map(float, roots)

def hermiteGaussWeightsFromZeros(n, roots):
  assert isinstance(n, int)
  require_numpy()
  roots = numpy.array(roots)
  weights = numpy.exp(-roots*roots/(n-1)) / (n * normalisedExtremeHermite(n-1, roots) ** 2)
  # Convert back to python float format for storage
  return map(float, weights)


def besselJZeros(m, a, b):
  require_mpmath()
  if not hasattr(mpmath, 'besseljzero'):
    besseljn = lambda x: mpmath.besselj(m, x)
    results = [mpmath.findroot(besseljn, mpmath.pi*(kp - 1./4 + 0.5*m)) for kp in range(a, b+1)]
  else:
    results = [mpmath.besseljzero(m, i) for i in xrange(a, b+1)]
  # Check that we haven't found double roots or missed a root. All roots should be separated by approximately pi
  assert all([0.6*mpmath.pi < (b - a) < 1.4*mpmath.pi for a, b in zip(results[:-1], results[1:])]), "Separation of Bessel zeros was incorrect."
  return results

def besselJWeightsFromZeros(m, roots):
  require_mpmath()
  prefactor = mpmath.mpf('2')  / (roots[-1]**2)
  return [prefactor / (mpmath.besselj(m+1, root))**2 for root in roots[:-1]]


class _MMT (_Transform):
  transformName = 'MMT'
  
  coordinateSpaceTag = DimensionRepresentation.registerTag('MMT coordinate space', parent = 'coordinate')
  spectralSpaceTag = DimensionRepresentation.registerTag('MMT spectral space', parent = 'spectral')
  auxiliarySpaceTag = DimensionRepresentation.registerTag('MMT auxiliary space', parent = 'auxiliary')
  
  def __init__(self, *args, **KWs):
    _Transform.__init__(self, *args, **KWs)
    self.basisMap = {}
    dataCache = self.getVar('dataCache')
    
    self.besselJZeroCache = dataCache.setdefault('besselJZeros', {})
  
  @property
  def children(self):
    children = super(_MMT, self).children
    [children.extend(basisDict['transformations'].values()) for basisDict in self.basisMap.values()]
    return children
  
  def globals(self):
    return '\n'.join([basisDict.get('globalsFunction')(dimName, basisDict) \
                          for dimName, basisDict in self.basisMap.items() if basisDict.get('globalsFunction')])
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   spectralLattice = None,
                   type = 'real', volumePrefactor = None,
                   xmlElement = None):
    assert type == 'real'
    assert transformName in ['bessel', 'spherical-bessel', 'hermite-gauss']
    if not spectralLattice:
      spectralLattice = lattice
    dim = super(_MMT, self).newDimension(name, max(lattice, spectralLattice), minimum, maximum,
                                         parent, transformName, aliases, 
                                         type, volumePrefactor, xmlElement)
    self.basisMap[dim.name] = transformName # Needs to be constructed basis here
    
    if transformName in ('bessel', 'spherical-bessel'):
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
            raise ParserException(xmlElement, "The 'order' attribute for Bessel transforms must be non-negative integers.")
      orderOffset = 0
      dimRepClass = BesselDimensionRepresentation
      
      if transformName == 'spherical-bessel':
        dimRepClass = SphericalBesselDimensionRepresentation
        if not self.hasattr('uselib'):
          self.uselib = []
        self.uselib.append('gsl')
        orderOffset = 0.5
      
      self.basisMap[dim.name] = dict(
        globalsFunction = self.besselGlobalsForDim,
        order = order,
        orderOffset = orderOffset,
        lattice = lattice,
        transformations = dict([
          ((name, 'k' + name), BesselBasis(parent = self, **self.argumentsToTemplateConstructors))
        ])
      )
      
      if not float(minimum) == 0.0:
        raise ParserException(xmlElement, "The domain for Bessel transform dimensions must begin at 0.")
      
      # Real space representation
      xspace = dimRepClass(name = name, type = type, lattice = lattice,
                           stepSizeArray = True, parent = dim,
                           tag = self.coordinateSpaceTag,
                           _maximum = maximum, _order = order,
                           **self.argumentsToTemplateConstructors)
      dim.addRepresentation(xspace)
      
      # Spectral space representation
      kspace = dimRepClass(name = 'k' + name, type = type, lattice = spectralLattice,
                           stepSizeArray = True, parent = dim,
                           _maximum = '(_besseljnorm_%(name)s/((real)%(maximum)s))' % locals(),
                           _order = order,
                           reductionMethod = dimRepClass.ReductionMethod.fixedStep,
                           tag = self.spectralSpaceTag,
                           **self.argumentsToTemplateConstructors)
      dim.addRepresentation(kspace)
      
    elif transformName == 'hermite-gauss':
      # Hermite-gauss basis (harmonic oscillator)
      coordinate2SpectralBasisChange = HermiteGaussEPBasis(parent = self, **self.argumentsToTemplateConstructors)
      fourier2SpectralBasisChange = HermiteGaussFourierEPBasis(parent = self, **self.argumentsToTemplateConstructors)
      
      self.basisMap[dim.name] = dict(
        globalsFunction = self.hermiteGaussGlobalsForDim,
        lattice = lattice,
        transformations = dict([
          ((name, 'n' + name), coordinate2SpectralBasisChange),
          ((name + '_4f', 'n' + name), coordinate2SpectralBasisChange),
          (('k' + name, 'n' + name), fourier2SpectralBasisChange)
        ])
      )
      
      if not float(minimum) == 0.0:
        raise ParserException(xmlElement, "For 'hermite-gauss' transformed dimensions, use the 'length_scale' attribute "
                                          "instead of 'domain'.")
      
      # Real space representation
      xspace = HermiteGaussDimensionRepresentation(
        name = name, type = type, lattice = lattice, _maximum = maximum,
        stepSizeArray = True, parent = dim, tag = self.coordinateSpaceTag,
        **self.argumentsToTemplateConstructors
      )
      dim.addRepresentation(xspace)
      
      # Spectral space representation
      nspace = UniformDimensionRepresentation(
        name = 'n' + name, type = 'long', lattice = spectralLattice,
        _minimum = '0', _maximum = spectralLattice, _stepSize = '1',
        parent = dim, tag = self.spectralSpaceTag,
        reductionMethod = UniformDimensionRepresentation.ReductionMethod.fixedStep,
        **self.argumentsToTemplateConstructors
      )
      dim.addRepresentation(nspace)
      
      # Fourier space representation
      # FIXME: We may want to make this have a fixedStep ReductionMethod, but that requires support from
      # the DimRep and from FourierTransformFFTW3MPI in the case that this dimension is distributed.
      kspace = HermiteGaussDimensionRepresentation(
        name = 'k' + name, type = type, lattice = lattice, _maximum = "(1.0 / (%s))" % maximum,
        stepSizeArray = True, parent = dim, tag = self.auxiliarySpaceTag,
        **self.argumentsToTemplateConstructors
      )
      dim.addRepresentation(kspace)
      
      fourFieldCoordinateSpace = HermiteGaussDimensionRepresentation(
        name = name + '_4f', type = type, lattice = lattice, _maximum = maximum,
        stepSizeArray = True, parent = dim, tag = self.auxiliarySpaceTag, fieldCount = 4.0,
        **self.argumentsToTemplateConstructors
      )
      dim.addRepresentation(fourFieldCoordinateSpace)
    return dim
  
  def availableTransformations(self):
    results = []
    geometry = self.getVar('geometry')
    # Sort dimension names based on their ordering in the geometry.
    sortedDimNames = [(geometry.indexOfDimensionName(dimName), dimName) for dimName in self.basisMap]
    sortedDimNames.sort()
    sortedDimNames = [o[1] for o in sortedDimNames]
    # Create all transforms just for each dimension individually
    for dimName, basisDict in self.basisMap.items():
      dimReps = geometry.dimensionWithName(dimName).representations
      for transformPair, basis in basisDict['transformations'].items():
        basisReps = [[rep for rep in dimReps if rep.name == repName][0] for repName in transformPair]
        results.append(dict(
          transformations = [transformPair],
          cost = reduce(operator.mul, [rep.lattice for rep in basisReps]),
          outOfPlace = True,
          transformFunction = basis.transformFunction,
          transformType = basis.matrixType,
        ))
    
    return results
  
  def besselJZeros(self, m, k):
    if not m in self.besselJZeroCache:
      self.besselJZeroCache[m] = besselJZeros(m, 1, k)
    else:
      if len(self.besselJZeroCache[m]) < k:
        self.besselJZeroCache[m].extend(besselJZeros(m, len(self.besselJZeroCache[m])+1, k))
    
    return self.besselJZeroCache[m][:k]
  
  def normalisedBesselJZeros(self, m, k):
    zeros = self.besselJZeros(m, k+1)
    norm = zeros[-1]
    return [zero/norm for zero in zeros[:-1]]
  
  def besselJWeights(self, m, k):
    return besselJWeightsFromZeros(m, self.besselJZeros(m, k+1))
  
  def hermiteZeros(self, n, _cache = {}):
    if not n in _cache:
      _cache[n] = hermiteZeros(n)
    return _cache[n]
  
  def hermiteGaussWeights(self, n, _cache = {}):
    if not n in _cache:
      _cache[n] = hermiteGaussWeightsFromZeros(n, self.hermiteZeros(n))
    return _cache[n]
  

