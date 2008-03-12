#!/usr/bin/env python
# encoding: utf-8
"""
_FilterOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from Operator import Operator
from ParserException import ParserException
from FieldElement import FieldElement

class _FilterOperator (Operator):
  operatorKind = Operator.OtherOperatorKind
  vectorsMustBeInSubsetsOfIntegrationField = False
  
  def __init__(self, *args, **KWs):
    Operator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.integratingMoments = True
  
  @property
  def defaultOperatorSpace(self):
    return 0
  
  def bindNamedVectors(self):
    super(_FilterOperator, self).bindNamedVectors()
    
    dependencies = self.vectorsFromEntity(self.dependenciesEntity)
    self.dependencies.update(dependencies)
    
  
  def preflight(self):
    super(_FilterOperator, self).preflight()
    
    if self.resultVector:
      # Add the result of our filter to the list of dependencies for our parent.
      self.parent.dependencies.add(self.resultVector)
    
    geometryTemplate = self.getVar('geometry')
    
    sourceFieldName = ''.join([self.parent.id, '_', self.name, '_source_field'])
    sourceField = FieldElement(name = sourceFieldName, **self.argumentsToTemplateConstructors)
    if self.dependenciesEntity:
      sourceField.xmlElement = self.dependenciesEntity.xmlElement
    else:
      sourceField.xmlElement = self.xmlElement
    
    sourceFieldDimensionNames = set()
    for dependency in self.dependencies:
      sourceFieldDimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    for fieldDimensionName in sourceFieldDimensionNames:
      if not sourceField.hasDimensionName(fieldDimensionName):
        sourceField.dimensions.append(geometryTemplate.dimensionWithName(fieldDimensionName))
    sourceField.sortDimensions()
    
    self.sourceField = sourceField
    
    if self.dependenciesEntity and self.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
       self.operatorSpace = self.sourceField.spaceFromString(self.dependenciesEntity.xmlElement.getAttribute('fourier_space'))
    # If the source field has the same dimensions as the target field,
    # (remember that the target field must be a subset of the source field)
    # Then we mustn't be doing any integration, and hence we don't need to
    # do any initialisation when doing the calculation of moments    
    if self.resultVector and sourceField.isSubsetOfField(self.resultVector.field):
     self.integratingMoments = False
    elif not self.resultVector:
     self.integratingMoments = False
    
  
  


