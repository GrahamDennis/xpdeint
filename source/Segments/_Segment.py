#!/usr/bin/env python
# encoding: utf-8
"""
_Segment.py

This contains all the pure-python code for segments

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from .ScriptElement import ScriptElement

class _Segment (ScriptElement):
  def __init__(self, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    
    self.segmentNumber = len(filter(lambda x: isinstance(x, _Segment), self.getVar('templates'))) - 1
    self.childSegments = []
    
    scriptElements = self.getVar('scriptElements')
    
    if not self in scriptElements:
      scriptElements.append(self)

  @property
  def name(self):
    return 'segment' + str(self.segmentNumber)
  
