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
  
  def __init__(self, *args, **KWs):
    localKWs = self.extractLocalKWs(['name', 'field', 'transformFree', 'initialBasis'], KWs)
    field = localKWs['field']
    self.name = localKWs['name']
    self.field = field
    if not 'parent' in KWs: KWs['parent'] = field
    
    if KWs['parent'] is field:
      field.managedVectors.add(self)
    else:
      field.temporaryVectors.add(self)
    
    ScriptElement.__init__(self, *args, **KWs)
    self.transformFree = localKWs.get('transformFree', False)
    
    # Set default variables
    self.components = []
    self._needsInitialisation = True
    self.type = 'complex'
    self.aliases = set()
    self.basesNeeded = set()
    self.initialBasis = None
    
    if localKWs.get('initialBasis') is not None:
      self.initialBasis = self.field.basisForBasis(localKWs['initialBasis'])
      self.basesNeeded.add(self.initialBasis)
    
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
    except (AttributeError, KeyError), err:
      return []
  
  @property
  def needsTransforms(self):
    if self.transformFree:
      return False
    return len(self.basesNeeded) > 1
  
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
  
  @lazy_property
  def allocSize(self):
    return '_' + self.id + '_alloc_size'
  
  def sizeInBasis(self, basis):
    return self.field.sizeInBasis(basis) + ' * _' + self.id + '_ncomponents'
  
  def sizeInBasisInReals(self, basis):
    if self.type == 'real':
      return self.sizeInBasis(basis)
    else:
      return '2 * ' + self.sizeInBasis(basis)
  
  def isTransformableTo(self, basis):
    if self.transformFree:
      return True
    return basis in self.transformMap['bases']
  
  def remove(self):
    self.field.managedVectors.discard(self)
    self.field.temporaryVectors.discard(self)
    
    super(_VectorElement, self).remove()


  