#!/usr/bin/env python
# encoding: utf-8
"""
_BesselTransform.py

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

from xpdeint.Features.Transforms.BesselBasis import BesselBasis

from xpdeint.Geometry.BesselDimensionRepresentation import BesselDimensionRepresentation
from xpdeint.Geometry.BesselNeumannDimensionRepresentation import BesselNeumannDimensionRepresentation
from xpdeint.Geometry.SphericalBesselDimensionRepresentation import SphericalBesselDimensionRepresentation

from xpdeint.ParserException import ParserException, error_missing_python_library

# We don't directly import mpmath so that mpmath isn't a requirement for xpdeint
# unless you use MMT's.
mpmath = None

# Again, don't directly import numpy
numpy = None
scipy = None


def require_mpmath():
  global mpmath
  if not mpmath:
    try:
      import mpmath
    except ImportError:
      error_missing_python_library("mpmath")
    
    if not hasattr(mpmath, 'besselj'):
      mpmath.besselj = mpmath.jn
    mpmath.mp.prec = 64
    

def require_numpy():
  global numpy
  if not numpy:
    try:
      import numpy
    except ImportError:
      error_missing_python_library("numpy")

def require_scipy():
  require_numpy()
  global scipy
  if not scipy:
    try:
      import scipy
      import scipy.special
      import scipy.optimize
    except ImportError:
      error_missing_python_library("scipy")

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

def besselJPrimeZeros(m, a, b):
  require_mpmath()
  results = [mpmath.besseljzero(m, i, derivative=1) for i in xrange(a, b+1)]
  return results

def besselNeumannMatrix(m, besseljzeros, besselValues, S):
  require_scipy()
  N = len(besseljzeros)
  matrix = numpy.zeros([N, N])
  for i in xrange(N):
    for j in xrange(N):
      matrix[i,j] = (2.0 / S) * scipy.special.jn(m, besseljzeros[i] * besseljzeros[j] / S) \
          / (besselValues[i] * besselValues[j])
  return matrix
  
def besselNeumannSFactor(m, besseljzeros):
  require_scipy()
  besseljzeros_for_matrix = besseljzeros[:-1]
  N = len(besseljzeros_for_matrix)
  print "Computing the Bessel-Neumann transform S factor for lattice size %i (this will be performed once and saved for each lattice size)..." % (N)
  besselValues = []
  for i in xrange(N):
    x = numpy.abs(scipy.special.jn(m, besseljzeros[i]))
    if m > 0:
      x *= numpy.sqrt(1.0 - m*m / (besseljzeros[i] * besseljzeros[i]))
    besselValues.append(x)

  def f(S):
    matrix = besselNeumannMatrix(m, besseljzeros_for_matrix, besselValues, S)
    determinant = numpy.linalg.det(matrix)
    result = numpy.abs(determinant) - 1.0
    return result
  
  S, results = scipy.optimize.brentq(f, besseljzeros[-2], besseljzeros[-1], full_output=True)
  return S


class _BesselTransform(MMT):
  transformName = 'BesselTransform'
  
  def __init__(self, *args, **KWs):
    MMT.__init__(self, *args, **KWs)
    dataCache = self.getVar('dataCache')
    
    self.besselJZeroCache = dataCache.setdefault('besselJZeros', {})
    self.besselJPrimeZeroCache = dataCache.setdefault('besselJPrimeZeros', {})
    self.besselNeumannSCache = dataCache.setdefault('besselNeumannSFactor', {})
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   spectralLattice = None,
                   type = 'real', volumePrefactor = None,
                   xmlElement = None):
    assert type == 'real'
    assert transformName in ['bessel', 'spherical-bessel', 'bessel-neumann']
    if not spectralLattice:
      spectralLattice = lattice
    dim = super(_BesselTransform, self).newDimension(name, max(lattice, spectralLattice), minimum, maximum,
                                                     parent, transformName, aliases, 
                                                     type, volumePrefactor, xmlElement)
    self.basisMap[dim.name] = transformName # Needs to be constructed basis here
    
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
    if transformName == 'bessel-neumann':
      weightOrder = order
      dimRepClass = BesselNeumannDimensionRepresentation
    else:
      weightOrder = order + 1
    
    if transformName == 'spherical-bessel':
      dimRepClass = SphericalBesselDimensionRepresentation
      if not self.hasattr('uselib'):
        self.uselib = []
      self.uselib.append('gsl')
      orderOffset = 0.5
    
    basis = BesselBasis(parent = self, **self.argumentsToTemplateConstructors)
    
    self.basisMap[dim.name] = dict(
      globalsFunction = self.globalsForDim,
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
    xspace = dimRepClass(name = name, type = type, runtimeLattice = lattice,
                         stepSizeArray = True, parent = dim,
                         tag = self.coordinateSpaceTag,
                         _maximum = maximum, _order = order, _weightOrder = weightOrder,
                         **self.argumentsToTemplateConstructors)
    dim.addRepresentation(xspace)
    
    # Spectral space representation
    kspace = dimRepClass(name = 'k' + name, type = type, runtimeLattice = spectralLattice,
                         stepSizeArray = True, parent = dim,
                         _maximum = '(_besseljS_%(name)s/((real)%(maximum)s))' % locals(),
                         _order = order, _weightOrder = weightOrder,
                         reductionMethod = dimRepClass.ReductionMethod.fixedStep,
                         tag = self.spectralSpaceTag,
                         **self.argumentsToTemplateConstructors)
    dim.addRepresentation(kspace)
    
    return dim
  
  def besselJZeros(self, m, k):
    if not m in self.besselJZeroCache:
      self.besselJZeroCache[m] = besselJZeros(m, 1, k)
    else:
      if len(self.besselJZeroCache[m]) < k:
        self.besselJZeroCache[m].extend(besselJZeros(m, len(self.besselJZeroCache[m])+1, k))
    
    return self.besselJZeroCache[m][:k]
  
  def besselJPrimeZeros(self, m, k):
    if not m in self.besselJPrimeZeroCache:
      self.besselJPrimeZeroCache[m] = besselJPrimeZeros(m, 1, k)
    else:
      if len(self.besselJPrimeZeroCache[m]) < k:
        self.besselJPrimeZeroCache[m].extend(besselJPrimeZeros(m, len(self.besselJPrimeZeroCache[m])+1, k))
    
    return self.besselJPrimeZeroCache[m][:k]
  
  def besselNeumannSFactor(self, m, k):
    require_numpy()
    if not (m, k) in self.besselNeumannSCache:
      zeros = map(numpy.double, self.besselJPrimeZeros(m, k+1))
      S = besselNeumannSFactor(m, zeros)
      self.besselNeumannSCache[(m, k)] = float(S)
    
    return self.besselNeumannSCache[(m, k)]
