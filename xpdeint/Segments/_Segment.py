#!/usr/bin/env python
# encoding: utf-8
"""
_Segment.py

This contains all the pure-python code for segments

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

from xpdeint.Function import Function
from xpdeint.Utilities import lazy_property
from xpdeint.CallOnceGuards import callOncePerInstanceGuard

class _Segment (ScriptElement):
  def __init__(self, *args, **KWs):
    if not 'parent' in KWs: KWs['parent'] = self.simulation
    ScriptElement.__init__(self, *args, **KWs)
    
    self.segmentNumber = len(filter(lambda x: isinstance(x, _Segment), self.getVar('templates'))) - 1
    self._childSegments = []
    self.parentSegment = None
    self.localCycles = 1
    self.name = 'segment' + str(self.segmentNumber)
    self._id = self.name # Override the id as the segments have unique numbering
    
    self.functions['segment'] = Function(name = '_segment' + str(self.segmentNumber),
                                         args = [], 
                                         implementation = self.segmentFunctionBody)
    
  
  @property
  def childSegments(self):
    return self._childSegments[:]
  
  @lazy_property
  def totalCycles(self):
    currSegment = self
    totalCycles = 1
    while currSegment:
      totalCycles *= currSegment.localCycles
      currSegment = currSegment.parentSegment
    return totalCycles
  
  def addSegment(self, seg):
    self._childSegments.append(seg)
    seg.parentSegment = self
  
  @callOncePerInstanceGuard
  def allocate(self):   return super(_Segment, self).allocate()
  @callOncePerInstanceGuard
  def free(self):       return super(_Segment, self).free()
  
  @callOncePerInstanceGuard
  def initialise(self): return super(_Segment, self).initialise()
  @callOncePerInstanceGuard
  def finalise(self):   return super(_Segment, self).finalise()

