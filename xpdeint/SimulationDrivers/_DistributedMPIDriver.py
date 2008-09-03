#!/usr/bin/env python
# encoding: utf-8
"""
_DistributedMPIDriver.py

Created by Graham Dennis on 2008-03-29.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.SimulationDrivers.SimulationDriver import SimulationDriver
from xpdeint.SimulationDrivers.MPI import MPI

from xpdeint.Features.BinaryOutput import BinaryOutput
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
  
  def mpiDimensionForSpace(self, space):
    return self._distributedTransform.mpiDimensionForSpace(space)
  
  def isFieldDistributed(self, field):
    return self._distributedTransform.isFieldDistributed(field)
  
  def sizeOfFieldInSpace(self, field, space):
    """Return a name of a variable the value of which is the size of `field` in `space`."""
    if self._distributedTransform.hasattr('sizeOfFieldInSpace'):
      return self._distributedTransform.sizeOfFieldInSpace(space)
    else:
      return field.allocSize
  
  def shadowedVariablesForField(self, field):
    if not self.isFieldDistributed(field):
      return []
    result = []
    for dim in field.dimensions:
      for rep in [rep for rep in dim.representations if rep and rep.hasLocalOffset]:
        result.extend([rep.localLattice, rep.localOffset])
    return result
  
  def setDistributedMPILatticeVariableForSpace(self, varName, spaceVarName):
    return self._distributedTransform.setDistributedMPILatticeVariableForSpace(varName, spaceVarName)
  
  def orderedDimensionsForFieldInSpace(self, field, space):
    """Return a list of the dimensions for field in the order in which they should be looped over"""
    if self._distributedTransform.hasattr('orderedDimensionsForFieldInSpace'):
      return self._distributedTransform.orderedDimensionsForFieldInSpace(field, space)
    return super(_DistributedMPIDriver, self).orderedDimensionsForFieldInSpace(field, space)
  
  
  def preflight(self):
    super(_DistributedMPIDriver, self).preflight()
    
    outputFeature = self.getVar('features')['Output']
    if not isinstance(outputFeature, BinaryOutput):
      raise ParserException(outputFeature.xmlElement, "The 'ascii' output format cannot be used with the 'distributed-mpi' driver.")
  
  
  
