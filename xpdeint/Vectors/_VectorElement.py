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
from xpdeint.Utilities import lazy_property

class _VectorElement (ScriptElement):
  isComputed = False
  
  def __init__(self, name, field, transformFree = False, *args, **KWs):
    if not 'parent' in KWs: KWs['parent'] = field
    
    self.name = name
    self.field = field
    
    if KWs['parent'] is field:
      field.managedVectors.add(self)
    else:
      field.temporaryVectors.add(self)
    
    ScriptElement.__init__(self, *args, **KWs)
    # Set default variables
    self.components = []
    self._needsInitialisation = True
    self._initialSpace = 0
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
                               args = [('unsigned long', 'newSpace')],
                               implementation = self.goSpaceFunctionContents,
                               predicate = lambda: self.needsTransforms)
    self.functions['goSpace'] = goSpaceFunction
  
  @property
  def dependencies(self):
    try:
      return self.initialiser.codeBlocks['initialisation'].dependencies
    except AttributeError:
      return []
  
  @property
  def needsTransforms(self):
    if self.transformFree:
      return False
    return len(self.spacesNeeded) > 1
  
  def __hash__(self):
    """
    Returns a hash of the vector element. This is used to ensure the ordering of vectors in sets remains the same between invocations.
    """
    return hash(self.id)
  
  @lazy_property
  def id(self):
    return ''.join([self.field.name, '_', self.name])
  
  @property
  def children(self):
    children = super(_VectorElement, self).children
    if self.initialiser:
      children.append(self.initialiser)
    return children
  
  @lazy_property
  def nComponents(self):
    return len(self.components)
  
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
    self._initialSpace = value & self.field.spaceMask
    self.spacesNeeded.add(value)
  
  # Create a property for the class with the above getter and setter methods
  initialSpace = property(_getInitialSpace, _setInitialSpace)
  del _getInitialSpace, _setInitialSpace
  
  @lazy_property
  def maxSizeInReals(self):
    if self.type == 'complex':
      multiplier = 2
    else:
      multiplier = 1
    return self.field.maxPoints * self.nComponents * multiplier
  
  @lazy_property
  def allocSize(self):
    return self.field.allocSize + ' * _' + self.id + '_ncomponents'
  
  def sizeInSpace(self, space):
    return self.field.sizeInSpace(space) + ' * _' + self.id + '_ncomponents'
  
  def sizeInSpaceInReals(self, space):
    if self.type == 'real':
      return self.sizeInSpace(space)
    else:
      return '2 * ' + self.sizeInSpace(space)
  
  def isTransformableTo(self, newSpace):
    if self.transformFree:
      return True
    newSpace &= self.field.spaceMask
    for dim in self.field.dimensions:
      if (newSpace ^ self.initialSpace) & dim.transformMask:
        if not dim.canTransformVector(self):
          # If the transform can't transform this vector, then
          # this vector can't be transformed to the new space
          return False
    return True
  
  def remove(self):
    self.field.managedVectors.discard(self)
    self.field.temporaryVectors.discard(self)
    
    super(_VectorElement, self).remove()


  