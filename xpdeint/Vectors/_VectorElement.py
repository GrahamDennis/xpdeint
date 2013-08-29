#!/usr/bin/env python
# encoding: utf-8
"""
_VectorElement.py

This contains all the pure-python code for VectorElement.tmpl

Created by Graham Dennis on 2007-10-17.

Copyright (c) 2007-2012, Graham Dennis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from xpdeint.ScriptElement import ScriptElement
from xpdeint.Geometry.FieldElement import FieldElement
from xpdeint.Vectors.VectorInitialisation import VectorInitialisation

from xpdeint.Function import Function
from xpdeint.Utilities import lazy_property

class _VectorElement (ScriptElement):
  isComputed = False
  isNoise = False
  
  def __init__(self, *args, **KWs):
    localKWs = self.extractLocalKWs(['name', 'field', 'initialBasis', 'type'], KWs)
    field = localKWs['field']
    self.name = localKWs['name']
    self.field = field
    if not 'parent' in KWs: KWs['parent'] = field
    
    if KWs['parent'] is field:
      field.managedVectors.add(self)
    else:
      field.temporaryVectors.add(self)
    
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.components = []
    self._needsInitialisation = True
    self._integratingComponents = False
    self.type = localKWs['type']
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
    
    basisTransformFunctionName = ''.join(['_', self.id, '_basis_transform'])
    basisTransformFunction = Function(name = basisTransformFunctionName,
                               args = [('ptrdiff_t', 'new_basis')],
                               implementation = self.basisTransformFunctionContents,
                               predicate = lambda: self.needsTransforms)
    self.functions['basisTransform'] = basisTransformFunction
  
  @property
  def dependencies(self):
    try:
      return self.initialiser.codeBlocks['initialisation'].dependencies
    except (AttributeError, KeyError), err:
      return []
  
  @property
  def needsTransforms(self):
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
  
  def _getIntegratingComponents(self):
    return self._integratingComponents
  
  def _setIntegratingComponents(self, value):
    self._integratingComponents = value
    # The computed vector only needs initialisation to zero if we are integrating.
    self.needsInitialisation = value
  
  integratingComponents = property(_getIntegratingComponents, _setIntegratingComponents)
  del _getIntegratingComponents, _setIntegratingComponents
  
  
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
    return basis in self.transformMap['bases']
  
  def remove(self):
    self.field.managedVectors.discard(self)
    self.field.temporaryVectors.discard(self)
    
    super(_VectorElement, self).remove()
  
  @property
  def primaryCodeBlock(self):
    try:
      return self.initialiser.codeBlocks['initialisation']
    except (AttributeError, KeyError), err:
      return None
  
  def preflight(self):
    super(_VectorElement, self).preflight()
    
    codeBlock = self.primaryCodeBlock
    if codeBlock:
      loopingDimensionNames = set([dim.name for dim in self.field.dimensions])
      for dependency in codeBlock.dependencies:
        loopingDimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
      codeBlock.field = FieldElement.sortedFieldWithDimensionNames(loopingDimensionNames)
    
      if codeBlock.dependenciesEntity and codeBlock.dependenciesEntity.xmlElement.hasAttribute('basis'):
        dependenciesXMLElement = codeBlock.dependenciesEntity.xmlElement
        codeBlock.basis = \
          codeBlock.field.basisFromString(
            dependenciesXMLElement.getAttribute('basis'),
            xmlElement = dependenciesXMLElement
          )
      
      # Because we have modified the codeBlock's field, we may also need to modify its basis.
      # We will take any missing elements from the new field's defaultCoordinateBasis
      codeBlock.basis = codeBlock.field.completedBasisForBasis(codeBlock.basis, codeBlock.field.defaultCoordinateBasis)
      
      self.initialBasis = self.field.basisForBasis(codeBlock.basis)
      self.basesNeeded.add(self.initialBasis)
    
      # Our components are constructed by an integral if the looping field doesn't have the same
      # dimensions as the field to which the computed vector belongs.
      if not codeBlock.field.isEquivalentToField(self.field):
        self.integratingComponents = True


  
