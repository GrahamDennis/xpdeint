#!/usr/bin/env python
# encoding: utf-8
"""
_Stepper.py

Created by Graham Dennis on 2008-11-12.

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

from xpdeint.ScriptElement import ScriptElement
from xpdeint.Utilities import lazy_property

class _Stepper (ScriptElement):
  @lazy_property
  def integrationVectors(self):
    return self.parent.integrationVectors
  
  @property
  def homeBasis(self):
    return self.parent.homeBasis
  
  @lazy_property
  def integrator(self):
    return self.parent
  
  @property
  def cross(self):
    return self.parent.cross
  
  def callFunction(self, functionName, *args, **KWs):
    return self.parent.functions[functionName].call(*args, **KWs)
  
  def localInitialise(self):
    return None
  
  def localFinalise(self):
    return None
  
  def reducedFieldCopy(self, *args, **KWs):
    return self.integrator.reducedFieldCopy(*args, **KWs)
  
  def updateDependenciesForNextStep(self, *args, **KWs):
    return self.integrator.updateDependenciesForNextStep(*args, **KWs)
  
