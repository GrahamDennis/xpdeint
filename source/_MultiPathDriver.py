#!/usr/bin/env python
# encoding: utf-8
"""
_MultiPathDriver.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from SimulationDriver import SimulationDriver

from VectorElement import VectorElement
from VectorInitialisation import VectorInitialisation

class _MultiPathDriver (SimulationDriver):
  logLevelsBeingLogged = "_PATH_LOG_LEVEL|_SIMULATION_LOG_LEVEL|_WARNING_LOG_LEVEL|_ERROR_LOG_LEVEL"
  
  def createNamedVectors(self):
    for mg in self.getVar('momentGroups'):
      sdVector = VectorElement(name = 'processed_sd', field = mg.outputField,
                               searchList = self.searchListTemplateArgument,
                               filter = self.filterTemplateArgument)
      sdVector.type = 'double'
      sdVector.needsInitialisation = True
      sdVector.nComponents = mg.processedVector.nComponents
      mg.outputField.managedVectors.add(sdVector)
    
    super(_MultiPathDriver, self).createNamedVectors()
  
  def rawVectorNeedsToBeAllocated(self, dict):
    """
    This function makes moment groups allocate their raw sampling vectors so that
    we can sample both the mean and the standard error.
    """
    dict['returnValue'] = True
  
