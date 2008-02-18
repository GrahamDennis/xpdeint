#!/usr/bin/env python
# encoding: utf-8
"""
_VectorElement.py

This contains all the pure-python code for VectorElement.tmpl

Created by Graham Dennis on 2007-10-17.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from ScriptElement import ScriptElement
from VectorInitialisation import VectorInitialisation

class _VectorElement (ScriptElement):
  def __init__(self, name, field, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    self.name = name
    self.field = field
    
    # Set default variables
    self.components = []
    self.needsFourierTransforms = False
    self.needsInitialisation = True
    self._initialSpace = 0
    self.nComponentsOverride = None
    self.type = 'complex'
    self.aliases = set()
    self.spacesNeeded = set()
    
    # Set default initialisation to be the zero initialisation template
    self.initialiser = VectorInitialisation(*args, **KWs)
    self.initialiser.vector = self
  
  @property
  def id(self):
    return ''.join([self.field.name, '_', self.name])
  
  def getNComponents(self):
    if self.nComponentsOverride:
      return self.nComponentsOverride
    return len(self.components)
  
  def setNComponents(self, value):
    self.nComponentsOverride = value
  
  # Create a property for the class with the above getter and setter methods
  nComponents = property(getNComponents, setNComponents)
  del getNComponents, setNComponents
  
  def getInitialSpace(self):
    return self._initialSpace
  
  def setInitialSpace(self, value):
    """
    Set the initial space for the vector.
    
    As a side-effect, this method also adds the initial space to the set of spaces
    that this vector is needed in.
    """
    self._initialSpace = value
    self.spacesNeeded.add(value)
  
  # Create a property for the class with the above getter and setter methods
  initialSpace = property(getInitialSpace, setInitialSpace)
  del getInitialSpace, setInitialSpace
  


  