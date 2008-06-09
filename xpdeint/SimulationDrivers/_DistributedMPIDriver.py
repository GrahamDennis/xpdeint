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
  
  def preflight(self):
    super(_DistributedMPIDriver, self).preflight()
    
    outputFeature = self.getVar('features')['Output']
    if not isinstance(outputFeature, BinaryOutput):
      raise ParserException(outputFeature.xmlElement, "The 'ascii' output format cannot be used with the 'distributed-mpi' driver.")
  
  def allocSizeOfField(self, field):
    if not self.isFieldDistributed(field):
      return super(_DistributedMPIDriver, self).allocSizeOfField(field)
    return ''.join(['_', field.name, '_alloc_size'])
  
