#!/usr/bin/env python
# encoding: utf-8
"""
_NoTransformMPI.py

Created by Graham Dennis on 2008-08-24.

Copyright (c) 2008-2012, Graham Dennis

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

from xpdeint.Features.Transforms._NoTransform import _NoTransform

class _NoTransformMPI (_NoTransform):
  def initialiseForMPIWithDimensions(self, dimensions):
    dimensions[0].representations[0].setHasLocalOffset()
    self.mpiDimension = dimensions[0]
    self._driver.distributedDimensionNames.append(self.mpiDimension.name)
  
  def isFieldDistributed(self, field):
    return field.hasDimension(self.mpiDimension)
  
  def canonicalBasisForBasis(self, basis, **KWs):
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
  

