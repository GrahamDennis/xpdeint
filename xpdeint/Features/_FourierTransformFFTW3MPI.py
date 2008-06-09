#!/usr/bin/env python
# encoding: utf-8
"""
_FourierTransformFFTW3MPI.py

Created by Graham Dennis on 2008-06-08.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.FourierTransformFFTW3 import FourierTransformFFTW3

from xpdeint.ParserException import ParserException

class _FourierTransformFFTW3MPI (FourierTransformFFTW3):
  def preflight(self):
    fields = self.getVar('fields')
    geometry = self.getVar('geometry')
    driver = self._driver
    
    # Check that all vectors that are distributed and need fourier transforms
    # contain all the points in the MPI dimensions. Otherwise we can't fourier
    # transform them.
    for field in filter(driver.isFieldDistributed, fields):
      # If all the distributed dimensions are the same in this field as in the geometry, then everything is OK
      if all([field.dimensionWithName(name) == geometry.dimensionWithName(name) for name in driver.distributedDimensionNames]):
        continue
      for vector in filter(lambda x: x.needsFourierTransforms, field.vectors):
        raise ParserException(vector.xmlElement, "Vector '%s' cannot be fourier transformed because it would be distributed with MPI\n"
                                                 "and it doesn't have the same number of points as the geometry for the distributed dimensions." % vector)
  
  def vectorNeedsPartialTransforms(self, vector):
    if not self._driver.isFieldDistributed(vector.field):
      return False
    if not vector.needsFourierTransforms:
      return False
    # If any of the spaces in which this vector is needed are not full spaces, then we need partial transforms
    if any([space != 0 and space != vector.field.spaceMask for space in vector.spacesNeeded]):
      return True
    return False
  
