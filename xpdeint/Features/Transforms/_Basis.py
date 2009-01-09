#!/usr/bin/env python
# encoding: utf-8
"""
_Basis.py

Created by Graham Dennis on 2008-12-14.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

from xpdeint.ParserException import ParserException

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
  besseljn = lambda x: mpmath.besselj(m, x)
  results = [mpmath.findroot(besseljn, mpmath.pi*(kp - 1./4 + 0.5*m)) for kp in range(a, b+1)]
  # Check that we haven't found double roots or missed a root. All roots should be separated by approximately pi
  assert all([0.6*mpmath.pi < (b - a) < 1.4*mpmath.pi for a, b in zip(results[:-1], results[1:])]), "Separation of Bessel zeros was incorrect."
  return results

def besselJWeightsFromZeros(m, roots):
  require_mpmath()
  prefactor = mpmath.mpf('2')  / (roots[-1]**2)
  return [prefactor / (mpmath.besselj(m+1, root))**2 for root in roots[:-1]]

class _Basis (ScriptElement):
  def __init__(self, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    
    dataCache = self.getVar('dataCache')
    
    self.besselJZeroCache = dataCache.setdefault('besselJZeros', {})
  
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
  

