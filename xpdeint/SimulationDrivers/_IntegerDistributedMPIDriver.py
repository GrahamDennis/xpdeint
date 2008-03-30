#!/usr/bin/env python
# encoding: utf-8
"""
_IntegerDistributedMPIDriver.py

Created by Graham Dennis on 2008-03-29.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.SimulationDrivers.DistributedMPIDriver import DistributedMPIDriver

import xpdeint.Geometry.IntegerDimension

class _IntegerDistributedMPIDriver (DistributedMPIDriver):
  def __init__(self, *args, **KWs):
    DistributedMPIDriver.__init__(self, *args, **KWs)
    
    transverseDimensions = filter(lambda x: x.transverse, self.getVar('geometry').dimensions)
    self.mpiDimension = transverseDimensions[0]
    assert isinstance(self.mpiDimension, xpdeint.Geometry.IntegerDimension.IntegerDimension)
    self.distributedDimensionNames.append(self.mpiDimension.name)
  
  def mpiDimensionForSpace(self, space):
    return self.mpiDimension
  

