#!/usr/bin/env python
# encoding: utf-8
"""
_FixedStep.py

Created by Graham Dennis on 2008-03-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from Integrator import Integrator

class _FixedStep (Integrator):
  # Is this integrator capable of doing cross-propagation integration?
  isCrossCapable = False
  
  def __init__(self, *args, **KWs):
    Integrator.__init__(self, *args, **KWs)
    
    # Set default variables
    self._cross = False
    self._step = None
    
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
  del _getCross, _setCross
  
  @property
  def bannedFeatures(self):
    """Return the features which are not permitted to be inserted by this instance."""
    
    # If we are cross-propagating, then ErrorCheck cannot simply subdivide the step.
    # And we don't want to sample anything for moment groups
    if self.cross:
      return ['ErrorCheck', 'Output']
    else:
      return None
  
  def _getStep(self):
    if self._step:
      return self._step
    return ''.join([str(self.interval), '/(double)', str(self.stepCount)])
  
  def _setStep(self, value):
    self._step = value
  
  step = property(_getStep, _setStep)
  del _getStep, _setStep
  
  def preflight(self):
    super(_FixedStep, self).preflight()
    # If we are cross-propagating, then we aren't a top-level script element, and so will be
    # called by the appropriate CrossPropagationOperator
    if self.cross:
      scriptElements = self.getVar('scriptElements')
      if self in scriptElements:
        scriptElements.remove(self)
    
  

