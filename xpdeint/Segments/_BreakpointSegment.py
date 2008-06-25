#!/usr/bin/env python
# encoding: utf-8
"""
_BreakpointSegment.py

Created by Graham Dennis on 2008-03-15.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Segments._Segment import _Segment

class _BreakpointSegment (_Segment):
  def __init__(self, *args, **KWs):
    _Segment.__init__(self, *args, **KWs)
    
    self.filename = None
    self.breakpointSpace = 0
    self.field = None
  
  @property
  def outputComponents(self):
    result = []
    for vector in self.orderedDependencies:
      for componentName in vector.components:
        result.append(componentName + 'R')
        if vector.type == 'complex':
          result.append(componentName + 'I')
    return result
  
  def bindNamedVectors(self):
    super(_Segment, self).bindNamedVectors()
    
    aVector = list(self.dependencies)[0]
    for vector in self.dependencies:
      if not vector.field.dimensions == aVector.field.dimensions:
        raise ParserException(self.xmlElement, "All vectors for a breakpoint element must be have the same dimensions.\n"
                                               "The conflicting vectors are: '%s' and '%s'." % (vector.name, aVector.name))
    self.field = aVector.field
    # We rely on a constant order for our dependencies when writing out
    self.orderedDependencies = list(self.dependencies)
  
  def preflight(self):
    super(_Segment, self).preflight()
    
    if self.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
      spaceString = self.dependenciesEntity.xmlElement.getAttribute('fourier_space')
      self.breakpointSpace = self.field.spaceFromString(spaceString, xmlElement = self.dependenciesEntity.xmlElement)
    
  

