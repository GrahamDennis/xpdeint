#!/usr/bin/env python
# encoding: utf-8
"""
_VectorElement.py

This contains all the pure-python code for VectorElement.tmpl

Created by Graham Dennis on 2007-10-17.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from ScriptElement import ScriptElement

class _VectorElement (ScriptElement):
  def __init__(self, name, field, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    self.name = name
    self.field = field
    
    # Set default variables
    self.components = []
    self.needsFourierTransforms = False
    self.needsInitialisation = True
    self.initialSpace = 0
    self.nComponentsOverride = None
    self.type = 'complex'
  
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
  