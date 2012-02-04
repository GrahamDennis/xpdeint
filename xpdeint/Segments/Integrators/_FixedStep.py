#!/usr/bin/env python
# encoding: utf-8
"""
_FixedStep.py

Created by Graham Dennis on 2008-03-01.

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

from xpdeint.Segments.Integrators.Integrator import Integrator

from xpdeint.Utilities import lazy_property

class _FixedStep (Integrator):
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
    if value and not self.stepper.isCrossCapable:
      raise AssertionError("This stepper (%s) does not support cross-propagation." % str(type(self.stepper)))
    else:
      self._cross = value
  
  cross = property(_getCross, _setCross)
  del _getCross, _setCross
  
  @lazy_property
  def bannedFeatures(self):
    """Return the features which are not permitted to be inserted by this instance."""
    
    # If we are cross-propagating, then ErrorCheck cannot simply subdivide the step.
    # And we don't want to sample anything for moment groups
    
    # GD: The reason that we disable auto-vectorisation is subtle, and I don't completely
    # understand it myself. But after much fiddling, it seems that the last step in the 
    # integrator where the results from the integration step are copied back into the main
    # array does not sync with the last memory write in the step (as the last step with the
    # auto-vectorisation feature would have been to a real*, so come time for the copy to
    # a complex variable, the CPU/compiler sees fit to reorder the stores causing all hell
    # to break loose). This isn't a particularly good explanation, but my understanding of
    # this isn't particularly strong.
    # 
    # My evidence is that everything works fine if I turn off auto-vectorisation, and it also
    # works fine if I have it on but have a printf before (but not after) the copy operation
    # (inside the loop) to force a read from the memory that is going to be written to and so force
    # the correct ordering between the two writes. It may be possible to turn on the
    # auto-vectorisation feature if a memory barrier is added before the final copy step, but I
    # don't know how to implement a cross-platform memory barrier, and I'm not about to find out.
    
    if self.cross:
      return ['ErrorCheck', 'Output', 'AutoVectorise']
    else:
      return None
  
  @lazy_property
  def step(self):
    return ''.join([str(self.interval), '/(real)', str(self.stepCount)])
  
  

