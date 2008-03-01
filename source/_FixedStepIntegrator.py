#!/usr/bin/env python
# encoding: utf-8
"""
_FixedStepIntegrator.py

Created by Graham Dennis on 2008-03-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from Integrator import Integrator

class _FixedStepIntegrator (Integrator):
  # Is this integrator capable of doing cross-propagation integration?
  isCrossCapable = False
  
  def __init__(self, *args, **KWs):
    Integrator.__init__(self, *args, **KWs)
    
    # Set default variables
    self._cross = False
    
    # Is this integrator being used as a cross-propagation integrator?
    self.cross = KWs.get('cross', False)
    
  
  def _getCross(self):
    return self._cross
  
  def _setCross(self, value):
    if value and not self.isCrossCapable:
      raise AssertionError("This class (%s) does not support cross-propagation." % str(type(self)))
    else:
      self._cross = value
  
  cross = property(_getCross, _setCross)
  
  @property
  def bannedFeatures(self):
    """Return the features which are not permitted to be inserted by this instance."""
    
    # If we are cross-propagating, then ErrorCheck cannot simply subdivide the step.
    if self.cross:
      return ['ErrorCheck']
    else:
      return None
