#!/usr/bin/env python
# encoding: utf-8
"""
_FilterSegment.py

Created by Graham Dennis on 2008-03-13.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Segments._Segment import _Segment

class _FilterSegment (_Segment):
  def __init__(self, *args, **KWs):
    _Segment.__init__(self, *args, **KWs)
    
    self.operatorContainers = []
  
  @property
  def children(self):
    children = super(_FilterSegment, self).children
    children.extend(self.operatorContainers)
    return children
  

