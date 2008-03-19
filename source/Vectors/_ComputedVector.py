#!/usr/bin/env python
# encoding: utf-8
"""
_ComputedVector.py

This contains all the pure-python code for ComputedVector.tmpl

Created by Graham Dennis on 2008-03-12.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from VectorElement import VectorElement

from .Geometry.FieldElement import FieldElement

class _ComputedVector (VectorElement):
  isComputed = True
  
  def __init__(self, *args, **KWs):
    VectorElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.loopingField = None
    self.dependenciesEntity = None
    self._integratingComponents = True
    self._evaluationSpace = 0
    self.evaluationCode = ''
  
  def _getEvaluationSpace(self):
    return self._evaluationSpace
  
  def _setEvaluationSpace(self, value):
    self._evaluationSpace = value
    self.initialSpace = value & self.field.spaceMask
  
  evaluationSpace = property(_getEvaluationSpace, _setEvaluationSpace)
  del _getEvaluationSpace, _setEvaluationSpace
  
  def _getIntegratingComponents(self):
    return self._integratingComponents
  
  def _setIntegratingComponents(self, value):
    self._integratingComponents = value
    # The computed vector only needs initialisation to zero if we are integrating.
    self.needsInitialisation = value
  
  integratingComponents = property(_getIntegratingComponents, _setIntegratingComponents)
  del _getIntegratingComponents, _setIntegratingComponents
  
  def bindNamedVectors(self):
    super(VectorElement, self).bindNamedVectors()
    
    self.dependencies.update(self.vectorsFromEntity(self.dependenciesEntity))
    
  def preflight(self):
    super(VectorElement, self).preflight()
    
    loopingDimensionNames = set()
    for dependency in self.dependencies:
      loopingDimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    self.loopingField = FieldElement.sortedFieldWithDimensionNames(loopingDimensionNames)
    
    if self.dependenciesEntity and self.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
      dependenciesXMLElement = self.dependenciesEntity.xmlElement
      self.evaluationSpace = self.loopingField.spaceFromString(dependenciesXMLElement.getAttribute('fourier_space'),
                                                               xmlElement = dependenciesXMLElement)
    
    # Our components are constructed by an integral if the looping field doesn't have the same
    # dimensions as the field to which the computed vector belongs.
    self.integratingComponents = not self.loopingField.isEquivalentToField(self.field)
  

