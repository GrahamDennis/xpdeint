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

def require_mpmath():
  global mpmath
  if not mpmath: import mpmath

def normalisedHermite(n, x):
  """Evaluate the normalised Hermite polynomial H_n(x)/(sqrt(n! 2^n sqrt(pi)))."""
  require_mpmath()
  orig = mpmath.mp.prec
  assert isinstance(n, int)
  x = mpmath.mpmathify(x)
  try:
    mpmath.mp.prec += 10
    hermites = [None, mpmath.mpf('0.0'), mpmath.power(mpmath.pi, -0.25)]
    for j in range(1, n+1):
      hermites[:2] = hermites[1:]
      hermites[2] = x * mpmath.sqrt(mpmath.mpf(2)/j) * hermites[1] \
                    - mpmath.sqrt(mpmath.mpf(j-1)/j) * hermites[0]
  finally:
    mpmath.mp.prec = orig
  return hermites[2]

def hermiteZeros(n):
  """Return the n zeros of the nth Hermite polynomial H_n(x)."""
  require_mpmath()
  assert isinstance(n, int)
  orig = mpmath.mp.prec
  try:
    # Determine the precision necessary to accurately determine the zeros.
    # The precision needed is equal to the precision needed to represent the amplitude
    # of the nth Hermite polynomial around its largest root.
    maxZeroGuess = mpmath.sqrt(2*n + 1) - 1.85575*mpmath.power(2*n+1, -mpmath.mpf('1')/6)
    mpmath.mp.dps = int(2*mpmath.log10(mpmath.exp(0.5*maxZeroGuess*maxZeroGuess)))
    
    # Because the roots are symmetric, only bother locating the positive roots.
    # Odd orders have zero as a root, so skip that too.
    positiveRoots = n//2
    roots = [None] * positiveRoots
    # Evaluate the roots from the largest to the smallest
    for j in range(positiveRoots):
      if j == 0:
        # Initial guess for largest root as per Numerical Recipes
        guess = mpmath.sqrt(2*n+1)-1.85575*mpmath.power(2*n+1, -mpmath.mpf('1')/6)
      elif j == 1:
        # Initial guess for second largest root assuming all roots equally spaced between the
        # maximum roots. Actually, they are more dense at the origin so this will be an upper bound.
        guess = roots[j-1]*(1 - mpmath.mpf('2')/n)
      else:
        # Initial guess for other roots using the previous guess less half the difference between
        # the last two roots
        guess = roots[j-1] - 0.5*(roots[j-2] - roots[j-1])
        # This guess could converge to the previous root. To prevent that, we divide out the last root
        # i.e. we solve for a root of H_n(x)/(x - x0) where x0 is the last root.
        # This will give us a better guess to use as a start for finding the root of H_n(x)
        # The root found of H_n(x)/(x-x0) should be the same as the root for H_n(x), but to avoid
        # any numerical errors, we use the root of H_n(x)/(x-x0) only as a very good initial guess
        # for finding a root of H_n(x)
        def f(x):
          return normalisedHermite(n, x)/(x-roots[j-1])
        
        def df(x):
          return mpmath.sqrt(2*n) * normalisedHermite(n-1, x)/(x-roots[j-1]) \
                 - normalisedHermite(n, x)/(x-roots[j-1])**2
        
        def d2f(x):
          return 2*mpmath.sqrt(n*(n-1)) * normalisedHermite(n-2, x)/(x-roots[j-1]) \
                 - mpmath.sqrt(2*n) * normalisedHermite(n-1, x)/(x-roots[j-1])**2  \
                 + 2 * normalisedHermite(n, x)/(x-roots[j-1])**3
        
        guess = mpmath.findroot(f, guess, df = df, d2f = d2f, solver = 'halley')
      roots[j] = mpmath.findroot(lambda x: normalisedHermite(n, x), guess,
                                 df = lambda x: mpmath.sqrt(2*n) * normalisedHermite(n-1, x),
                                 d2f = lambda x: 2*mpmath.sqrt(n*(n-1)) * normalisedHermite(n-2, x),
                                 solver = 'halley')
      assert roots[j] > 0.0, "Failed to find Hermite roots"
    roots.extend([-root for root in roots])
    # If n is odd, there is a zero root as well
    if (n % 2) == 1:
      roots.append(mpmath.mpf('0'))
    roots.sort()
    assert len(roots) == n
  finally:
    mpmath.mp.prec = orig
  return roots


def hermiteGaussWeightsFromZeros(n, roots):
  require_mpmath()
  assert isinstance(n, int)
  orig = mpmath.mp.prec
  try:
    maxRoot = max(roots)
    mpmath.mp.dps = int(2*mpmath.log10(mpmath.exp(0.5*maxRoot*maxRoot)))
    
    weights = [mpmath.exp(root * root) / (n * (normalisedHermite(n-1, root) ** 2)) for root in roots]
  finally:
    mpmath.mp.prec = orig
  return weights

def besselJZeros(m, a, b):
  require_mpmath()
  besseljn = lambda x: mpmath.besselj(m, x)
  results = [mpmath.findroot(besseljn, mpmath.pi*(kp - 1./4 + 0.5*m)) for kp in range(a, b+1)]
  # Check that we haven't found double roots or missed a root. All roots should be separated by approximately pi
  assert all([0.6*mpmath.pi < (b - a) < 1.4*mpmath.pi for a, b in zip(result[:-1], result[1:])]), "Separation of Bessel zeros was incorrect."
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
    self.hermiteZeroCache = dataCache.setdefault('hermiteZeros', {})
    self.hermiteGaussWeightsCache = dataCache.setdefault('hermiteGaussWeights', {})
  
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
  
  def hermiteZeros(self, n):
    if not n in self.hermiteZeroCache:
      # Just over-engineering a bit. Ensure the correct suffix is displayed
      # for the number n
      suffix = 'th'
      if n < 10 or n > 20:
        suffixMap = {1: 'st', 2: 'nd', 3: 'rd'}
        suffix = suffixMap.get(n % 10, 'th')
      print "Finding roots of the %(n)i%(suffix)s Hermite polynomial (this can take a while)..." % locals()
      self.hermiteZeroCache[n] = hermiteZeros(n)
      print "... roots found."
    return self.hermiteZeroCache[n]
  
  def hermiteGaussWeights(self, n):
    if not n in self.hermiteGaussWeightsCache:
      self.hermiteGaussWeightsCache[n] = hermiteGaussWeightsFromZeros(n, self.hermiteZeros(n))
    return self.hermiteGaussWeightsCache[n]
  

