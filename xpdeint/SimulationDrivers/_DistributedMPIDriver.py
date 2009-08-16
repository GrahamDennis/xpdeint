#!/usr/bin/env python
# encoding: utf-8
"""
_DistributedMPIDriver.py

Created by Graham Dennis on 2008-03-29.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.SimulationDrivers.SimulationDriver import SimulationDriver
from xpdeint.SimulationDrivers.MPI import MPI

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
  
  def preflight(self):
    super(_DistributedMPIDriver, self).preflight()
    
    outputFeature = self.getVar('features')['Output']
    outputFormat = outputFeature.outputFormat
    
    # FIXME: This is dodgy
    if not outputFormat.mpiSafe:
      raise ParserException(outputFeature.xmlElement, "The '%s' output format cannot be used with the 'distributed-mpi' driver." % outputFormat.name)
  
  def canonicalBasisForBasis(self, basis, **KWs):
    if self._distributedTransform.hasattr('canonicalBasisForBasis'):
      return self._distributedTransform.canonicalBasisForBasis(basis, **KWs)
    return super(_DistributedMPIDriver, self).canonicalBasisForBasis(basis, **KWs)
  
