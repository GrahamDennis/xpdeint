#!/usr/bin/env python
# encoding: utf-8
"""
_NoTransformMPI.py

Created by Graham Dennis on 2008-08-24.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms._NoTransform import _NoTransform

class _NoTransformMPI (_NoTransform):
  def initialiseForMPIWithDimensions(self, dimensions):
    dimensions[0].representations[0].setHasLocalOffset()
    self.mpiDimension = dimensions[0]
    self._driver.distributedDimensionNames.append(self.mpiDimension.name)
  
  def isFieldDistributed(self, field):
    return field.hasDimension(self.mpiDimension)
  
  def canonicalBasisForBasis(self, basis):
    mpiDimRep = self.mpiDimension.representations[0]
    mpiDimNames = set([mpiDimRep.name, mpiDimRep.canonicalName])
    if mpiDimNames.intersection(basis):
      basis = list(basis)
      for idx, b in enumerate(basis[:]):
        if b in mpiDimNames:
          basis[idx] = mpiDimRep.canonicalName
          break
      basis = tuple(basis)
    return basis
  

