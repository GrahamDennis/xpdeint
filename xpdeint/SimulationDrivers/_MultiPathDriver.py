#!/usr/bin/env python
# encoding: utf-8
"""
_MultiPathDriver.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.SimulationDrivers.SimulationDriver import SimulationDriver

from xpdeint.Vectors.VectorElement import VectorElement
from xpdeint.Vectors.VectorInitialisation import VectorInitialisation

class _MultiPathDriver (SimulationDriver):
  logLevelsBeingLogged = "_PATH_LOG_LEVEL|_SIMULATION_LOG_LEVEL|_WARNING_LOG_LEVEL|_ERROR_LOG_LEVEL"
  
  def preflight(self):
    super(_MultiPathDriver, self).preflight()
    
    for mg in self.getVar('momentGroups'):
      mg.processedVector.aliases.add('_%s_sd' % mg.outputField.name)
    
  
  def rawVectorNeedsToBeAllocated(self, dict):
    """
    This function makes moment groups allocate their raw sampling vectors so that
    we can sample both the mean and the standard error.
    """
    dict['returnValue'] = True
  
