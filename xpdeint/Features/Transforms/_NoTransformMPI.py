#!/usr/bin/env python
# encoding: utf-8
"""
_NoTransformMPI.py

Created by Graham Dennis on 2008-08-24.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms._NoTransform import _NoTransform

from xpdeint.Geometry._Dimension import _Dimension
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation

class _NoTransformMPI (_NoTransform):
  def initialiseForMPIWithDimensions(self, dimensions):
    dimensions[0].inSpace(0).setHasLocalOffset()
    self.mpiDimension = dimensions[0]
    self._driver.distributedDimensionNames.append(self.mpiDimension.name)
  
  def isFieldDistributed(self, field):
    return field.hasDimension(self.mpiDimension)
  
  def mpiDimensionForSpace(self, space):
    return self.mpiDimension
  

