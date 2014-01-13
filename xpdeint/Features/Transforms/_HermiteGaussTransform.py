#!/usr/bin/env python
# encoding: utf-8
"""
_HermiteGaussTransform.py

Created by Graham Dennis on 2013-11-26.

Copyright (c) 2013, Graham Dennis

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

from xpdeint.Features.Transforms.MMT import MMT

from xpdeint.Features.Transforms.HermiteGaussEPBasis import HermiteGaussEPBasis
from xpdeint.Features.Transforms.HermiteGaussFourierEPBasis import HermiteGaussFourierEPBasis
from xpdeint.Features.Transforms.HermiteGaussTwiddleBasis import HermiteGaussTwiddleBasis

from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.HermiteGaussDimensionRepresentation import HermiteGaussDimensionRepresentation

from xpdeint.ParserException import ParserException

# We don't directly import numpy so that numpy isn't a requirement for xpdeint
# unless you use MMT's.
numpy = None

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

class _HermiteGaussTransform(MMT):
  transformName = 'HermiteGaussTransform'
  
  def __init__(self, *args, **KWs):
    MMT.__init__(self, *args, **KWs)
    dataCache = self.getVar('dataCache')
    
    self.hermiteCache = dataCache.setdefault('hermiteGauss', {})
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   spectralLattice = None,
                   type = 'real', volumePrefactor = None,
                   xmlElement = None):
    assert type == 'real'
    assert transformName in ['hermite-gauss']
    if not spectralLattice:
      spectralLattice = lattice
    dim = super(_HermiteGaussTransform, self).newDimension(name, max(lattice, spectralLattice), minimum, maximum,
                                                           parent, transformName, aliases, 
                                                           type, volumePrefactor, xmlElement)
    self.basisMap[dim.name] = transformName # Needs to be constructed basis here
    
    # Hermite-gauss basis (harmonic oscillator)
    coordinate2SpectralBasisChange = HermiteGaussEPBasis(parent = self, **self.argumentsToTemplateConstructors)
    spectralBasisTwiddleChange = HermiteGaussTwiddleBasis(parent = self, **self.argumentsToTemplateConstructors)
    # This is how we used to do 'nx' -> 'kx' transforms
    fourier2SpectralBasisChange = HermiteGaussFourierEPBasis(parent = self, **self.argumentsToTemplateConstructors)
    
    self.basisMap[dim.name] = dict(
      globalsFunction = self.globalsForDim,
      lattice = lattice,
      transformations = dict([
        ((name, 'n' + name), coordinate2SpectralBasisChange),
        ((name + '_4f', 'n' + name), coordinate2SpectralBasisChange),
        (('k' + name, 'n' + name + '_twiddle'), coordinate2SpectralBasisChange),
        (('n' + name, 'n' + name + '_twiddle'), spectralBasisTwiddleChange),
        # This is how the 'nx' -> 'kx' transforms used to be done, but it's slower.
        # This transform should never be chosen because the cost estimates should prevent it, but we keep it here
        # anyway for reference.
        (('k' + name, 'n' + name), fourier2SpectralBasisChange)
      ])
    )
    
    if not float(minimum) == 0.0:
      raise ParserException(xmlElement, "For 'hermite-gauss' transformed dimensions, use the 'length_scale' attribute "
                                        "instead of 'domain'.")
    
    # Real space representation
    xspace = HermiteGaussDimensionRepresentation(
      name = name, type = type, runtimeLattice = lattice, _maximum = maximum,
      stepSizeArray = True, parent = dim, tag = self.coordinateSpaceTag,
      **self.argumentsToTemplateConstructors
    )
    dim.addRepresentation(xspace)
    
    # Spectral space representation
    nspace = UniformDimensionRepresentation(
      name = 'n' + name, type = 'long', runtimeLattice = spectralLattice,
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
      name = 'k' + name, type = type, runtimeLattice = lattice, _maximum = "(1.0 / (%s))" % maximum,
      stepSizeArray = True, parent = dim, tag = self.auxiliarySpaceTag,
      **self.argumentsToTemplateConstructors
    )
    dim.addRepresentation(kspace)
    
    twiddleSpace = UniformDimensionRepresentation(
        name = 'n' + name + '_twiddle', type = 'long', runtimeLattice = spectralLattice,
        _minimum = '0', _maximum = spectralLattice, _stepSize = '1',
        parent = dim, tag = self.auxiliarySpaceTag,
        reductionMethod = UniformDimensionRepresentation.ReductionMethod.fixedStep,
        **self.argumentsToTemplateConstructors
    )
    dim.addRepresentation(twiddleSpace)
    
    fourFieldCoordinateSpace = HermiteGaussDimensionRepresentation(
      name = name + '_4f', type = type, runtimeLattice = lattice, _maximum = maximum,
      stepSizeArray = True, parent = dim, tag = self.auxiliarySpaceTag, fieldCount = 4.0,
      **self.argumentsToTemplateConstructors
    )
    dim.addRepresentation(fourFieldCoordinateSpace)
    return dim
  
  def hermiteZeros(self, n):
    zerosCache = self.hermiteCache.setdefault('zeros',{})
    if not n in zerosCache:
      zerosCache[n] = hermiteZeros(n)
    return zerosCache[n]
  
  def hermiteGaussWeights(self, n):
    weightsCache = self.hermiteCache.setdefault('weights',{})
    if not n in weightsCache:
      weightsCache[n] = hermiteGaussWeightsFromZeros(n, self.hermiteZeros(n))
    return weightsCache[n]
  

