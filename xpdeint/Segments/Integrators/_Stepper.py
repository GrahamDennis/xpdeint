#!/usr/bin/env python
# encoding: utf-8
"""
_Stepper.py

Created by Graham Dennis on 2008-11-12.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
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
  
