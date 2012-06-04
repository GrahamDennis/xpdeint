#!/usr/bin/env python
# encoding: utf-8
"""
_DistributedMPIDriver.py

Created by Graham Dennis on 2008-03-29.

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

from xpdeint.SimulationDrivers.SimulationDriver import SimulationDriver
from xpdeint.SimulationDrivers.MPI import MPI
from xpdeint.Features.OutputFormat import OutputFormat

from xpdeint.ParserException import ParserException

class _DistributedMPIDriver (SimulationDriver, MPI):
  def __init__(self, *args, **KWs):
    SimulationDriver.__init__(self, *args, **KWs)
    MPI.__init__(self, *args, **KWs)
    
    self._distributedTransform = None
  
  def _getDistributedTransform(self):
    return self._distributedTransform
  
  def _setDistributedTransform(self, value):
    assert not self._distributedTransform
    self._distributedTransform = value
  
  distributedTransform = property(_getDistributedTransform, _setDistributedTransform)
  del _getDistributedTransform, _setDistributedTransform
  
  def isFieldDistributed(self, field):
    return self._distributedTransform.isFieldDistributed(field)
  
  def shadowedVariablesForField(self, field):
    if not self.isFieldDistributed(field):
      return []
    result = []
    for dim in field.dimensions:
      for rep in [rep for rep in dim.representations if rep and rep.hasLocalOffset]:
        result.extend([rep.localLattice, rep.localOffset])
    return result
  
  def basisWithTransverseDimensionsMovedAfterMPIDimensions(self, basis):
    geometry = self.getVar('geometry')
    dimRepNameMap = dict()
    for dim in geometry.dimensions:
      for dimRep in dim.representations:
        dimRepNameMap[dimRep.canonicalName] = dim
        dimRepNameMap[dimRep.name] = dim
    basis = list(basis)
    for dimRepName in basis[:]:
      if dimRepNameMap[dimRepName].transverse and dimRepNameMap[dimRepName].name not in self.distributedDimensionNames:
        # Move it to the end.
        basis.remove(dimRepName)
        basis.append(dimRepName)
    return tuple(basis)
  
  def preflight(self):
    super(_DistributedMPIDriver, self).preflight()
    
    outputFormats = [o for o in self.getVar('templates') if isinstance(o, OutputFormat)]
    outputFeature = self.getVar('features')['Output']
    
    for outputFormat in outputFormats:
      if not outputFormat.mpiSafe:
        raise ParserException(outputFeature.xmlElement, "The '%s' output format cannot be used with the 'distributed-mpi' driver." % outputFormat.name)
  
  def canonicalBasisForBasis(self, basis, **KWs):
    basis = self.basisWithTransverseDimensionsMovedAfterMPIDimensions(basis)
    if self._distributedTransform.hasattr('canonicalBasisForBasis'):
      return self._distributedTransform.canonicalBasisForBasis(basis, **KWs)
    return super(_DistributedMPIDriver, self).canonicalBasisForBasis(basis, **KWs)
  
