#!/usr/bin/env python
# encoding: utf-8
"""
_MPIMultiPathDriver.py

Created by Graham Dennis on 2008-03-28.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.SimulationDrivers.MultiPathDriver import MultiPathDriver
from xpdeint.SimulationDrivers.MPI import MPI

class _MPIMultiPathDriver (MultiPathDriver, MPI):
  def __init__(self, *args, **KWs):
    MultiPathDriver.__init__(self, *args, **KWs)
    MPI.__init__(self, *args, **KWs)
  
