#!/usr/bin/env python
# encoding: utf-8
"""
_VectorElement.py

This contains all the pure-python code for VectorElement.tmpl

Created by Graham Dennis on 2007-10-17.
Copyright (c) 2007-2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement
from xpdeint.Vectors.VectorInitialisation import VectorInitialisation

from xpdeint.Function import Function

class _VectorElement (ScriptElement):
  isComputed = False
  
  def __init__(self, name, field, transformFree = False, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    self.name = name
    self.field = field
    
    # Set default variables
    self.components = []
    self._needsInitialisation = True
    self._initialSpace = 0
    self.nComponentsOverride = None
    self.type = 'complex'
    self.aliases = set()
    self.spacesNeeded = set()
    self.transformFree = transformFree
    
    # Set default initialisation to be the zero initialisation template
    self.initialiser = VectorInitialisation(*args, **KWs)
    self.initialiser.vector = self
    
    intialiseFunctionName = ''.join(['_', self.id, '_initialise'])
    initialiseFunction = Function(name = intialiseFunctionName,
                                  args = [],
                                  implementation = self.initialiseFunctionContents,
                                  description = 'initialisation for ' + self.description(),
                                  predicate = lambda: self.needsInitialisation)
    self.functions['initialise'] = initialiseFunction
    
    goSpaceFunctionName = ''.join(['_', self.id, '_go_space'])
    goSpaceFunction = Function(name = goSpaceFunctionName,
                               args = [('unsigned long', '_newSpace')],
                               implementation = self.goSpaceFunctionContents,
                               predicate = lambda: self.needsTransforms)
    self.functions['goSpace'] = goSpaceFunction
    
    
  
  @property
  def needsTransforms(self):
    if self.transformFree:
      return False
    return len(self.spacesNeeded) > 1
  
  @property
  def id(self):
    return ''.join([self.field.name, '_', self.name])
  
  @property
  def children(self):
    if self.initialiser:
      return [self.initialiser]
    return []
  
  def _getNComponents(self):
    if self.nComponentsOverride:
      return self.nComponentsOverride
    return len(self.components)
  
  def _setNComponents(self, value):
    self.nComponentsOverride = value
  
  # Create a property for the class with the above getter and setter methods
  nComponents = property(_getNComponents, _setNComponents)
  del _getNComponents, _setNComponents
  
  def _getNeedsInitialisation(self):
    return self._needsInitialisation
  
  def _setNeedsInitialisation(self, value):
    self._needsInitialisation = value
    if not value and self.initialiser:
      self.initialiser.vector = None
      self.initialiser.remove()
      self.initialiser = None
  
  # Create a property for the class with the above getter and setter methods
  needsInitialisation = property(_getNeedsInitialisation, _setNeedsInitialisation)
  del _getNeedsInitialisation, _setNeedsInitialisation
  
  def _getInitialSpace(self):
    return self._initialSpace
  
  def _setInitialSpace(self, value):
    """
    Set the initial space for the vector.
    
    As a side-effect, this method also adds the initial space to the set of spaces
    that this vector is needed in.
    """
    self._initialSpace = value
    self.spacesNeeded.add(value)
  
  # Create a property for the class with the above getter and setter methods
  initialSpace = property(_getInitialSpace, _setInitialSpace)
  del _getInitialSpace, _setInitialSpace
  
  @property
  def maxSizeInReals(self):
    if self.type == 'complex':
      multiplier = 2
    else:
      multiplier = 1
    return self.field.maxPoints * self.nComponents * multiplier
  
  def isTransformableTo(self, newSpace):
    if self.transformFree:
      return True
    newSpace &= self.field.spaceMask
    for dim in self.field.dimensions:
      if (newSpace ^ self.initialSpace) & dim.transformMask:
        if not dim.transform.canTransformVectorInDimension(self, dim):
          # If the transform can't transform this vector, then
          # this vector can't be transformed to the new space
          return False
    return True
  


  