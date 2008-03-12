#!/usr/bin/env python
# encoding: utf-8
"""
_ComputedVector.py

This contains all the pure-python code for ComputedVector.tmpl

Created by Graham Dennis on 2008-03-12.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from VectorElement import VectorElement

from FieldElement import FieldElement

class _ComputedVector (VectorElement):
  isComputed = True
  
  def __init__(self, *args, **KWs):
    VectorElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.loopingField = None
    self.dependenciesEntity = None
    self.integratingComponents = True
    self.evaluationSpace = 0
  
  
  def bindNamedVectors(self):
    super(VectorElement, self).bindNamedVectors()
    
    self.dependencies.update(self.vectorsFromEntity(self.dependenciesEntity))
    
  def preflight(self):
    super(VectorElement, self).preflight()
    
    loopingDimensionNames = set()
    for dependency in self.dependencies:
      loopingDimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    loopingFieldName = ''.join([self.id, '_looping_field'])
    self.loopingField = FieldElement(name = loopingFieldName, **self.argumentsToTemplateConstructors)
    
    geometryTemplate = self.getVar('geometry')
    
    for dimensionName in loopingDimensionNames:
      self.loopingField.dimensions.append(geometryTemplate.dimensionWithName(dimensionName))
    self.loopingField.sortDimensions()
    
    dependenciesXMLElement = self.dependenciesEntity.xmlElement
    self.loopingField.xmlElement = dependenciesXMLElement
    
    if dependenciesXMLElement.hasAttribute('fourier_space'):
      self.evaluationSpace = self.loopingField.spaceFromString(dependenciesXMLElement.getAttribute('fourier_space'))
      self.initialSpace = self.evaluationSpace & self.field.spaceMask
    
    # Our components are constructed by an integral if the looping field doesn't have the same
    # dimensions as the field to which the computed vector belongs.
    self.integratingComponents = not self.loopingField.isEquivalentToField(self.field)
    # The computed vector only needs initialisation to zero if we are integrating.
    self.needsInitialisation = self.integratingComponents
  

