#!/usr/bin/env python
# encoding: utf-8
"""
_DimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

class _DimensionRepresentation(ScriptElement):
  """
  See the documentation for the `_Dimension` class for more details, but the idea here is that
  the details of the geometry of a dimension in a given space are controlled by a dimension
  'representation'. This class controls the creation of loops over the dimension, the creation
  of variables for the lattice, minimum and maximum of the representation. Further things like
  how exactly to split the dimension are controlled by the transform that created the representation.
  """
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['name', 'type', 'lattice'], KWs)
    ScriptElement.__init__(self, **KWs)
    
    self.name = localKWs['name']
    
    self.type = localKWs['type']
    self.lattice = localKWs.get('lattice', 0)
    
  
  def __eq__(self, other):
    try:
      return (self.name == other.name and
              self.type == other.type and
              self.lattice == other.lattice)
    except AttributeError:
      return NotImplemented
  
  def __ne__(self, other):
    eq = self.__eq__(other)
    if eq is NotImplemented:
      return NotImplemented
    else:
      return not eq
  
  def _newInstanceDict(self):
    return {'name': self.name, 'type': self.type, 'lattice': self.lattice}
  
  def copy(self):
    newInstanceDict = self._newInstanceDict()
    newInstanceDict.update(self.argumentsToTemplateConstructors)
    return self.__class__(**newInstanceDict)
  
  @property
  def prefix(self):
    return self.parent.prefix
  
  @property
  def globalLattice(self):
    return self.prefix + '_lattice_' + self.name
  
  @property
  def mayHaveLocalOffset(self):
    # FIXME: Implement this
    return False
  
  @property
  def localLattice(self):
    # FIXME: Implement this properly
    return self.globalLattice
  
  @property
  def localOffset(self):
    # FIXME: Implement this properly
    return '0'
  
  @property
  def minimum(self):
    return self.prefix + '_min_' + self.name
  
  @property
  def maximum(self):
    return self.prefix + '_max_' + self.name
  
  @property
  def stepSize(self):
    return self.prefix + '_d' + self.name
  
  @property
  def loopIndex(self):
    return '_index_' + self.name
  
  

