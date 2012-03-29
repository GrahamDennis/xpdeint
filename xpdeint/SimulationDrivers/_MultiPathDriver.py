#!/usr/bin/env python
# encoding: utf-8
"""
_MultiPathDriver.py

Created by Graham Dennis on 2008-02-02.

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

class _MultiPathDriver (SimulationDriver):
  logLevelsBeingLogged = "_PATH_LOG_LEVEL|_SIMULATION_LOG_LEVEL|_WARNING_LOG_LEVEL|_ERROR_LOG_LEVEL|_NO_ERROR_TERMINATE_LOG_LEVEL"
  
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
  
