#!/usr/bin/env python
# encoding: utf-8
"""
_CrossPropagationOperator.py

Created by Graham Dennis on 2008-03-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.Operator import Operator

from xpdeint.Geometry.FieldElement import FieldElement
from xpdeint.Vectors.VectorElement import VectorElement

from xpdeint.ParserException import ParserException

class _CrossPropagationOperator (Operator):
  operatorKind = Operator.OtherOperatorKind
  evaluateOperatorFunctionArguments = []
  
  # This is a class attribute and not an instance attribute to prevent two
  # cross-propagation operators trying to create the same reduced field
  # and then creating the same reduced vectors, but in these different
  # fields (but with the same names)
  # By having a sharedFieldMap, two cross-propagators with the same cross-propagation
  # dimension can share the same fieldMap variable.
  # sharedFieldMap is a map from propagation dimension name to a dictionary that can
  # be used as the fieldMap variable for an instance
  sharedFieldMap = {}
  
  def __init__(self, *args, **KWs):
    Operator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.propagationDirection = None # '+' or '-'
    self.propagationDimension = None # Name of the propagation dimension
    
    self._crossPropagationIntegrator = None
    self.crossPropagationIntegratorDeltaAOperator = None
    self.boundaryConditionDependenciesEntity = None
    self.boundaryConditionDependencies = set()
    self.boundaryConditionCode = None
    self.integrationVectorsEntity = None
    self.integrationVectors = set()
    self.dependencyMap = {}
    self.integrationVectorMap = {}
    self.reducedField = None
    self._fieldMap = None
  
  
  @property
  def operatorSpace(self):
    return 0
  
  @property
  def fieldMap(self):
    """
    Return the field map for this cross-propagator.
    
    The fieldMap is a map from full fields to reduced cross-propagation fields that do not have the
    cross-propagation dimension. The fieldMap instances are shared between cross-propagators that have
    the same cross-propagation dimension.
    """
    if not self._fieldMap:
      if not self.propagationDimension in self.sharedFieldMap:
        self._fieldMap = self.sharedFieldMap[self.propagationDimension] = {}
      else:
        self._fieldMap = self.sharedFieldMap[self.propagationDimension]
    
    return self._fieldMap
  
  def _getCrossPropagationIntegrator(self):
    return self._crossPropagationIntegrator
  
  def _setCrossPropagationIntegrator(self, value):
    self._crossPropagationIntegrator = value
    if value not in self._children:
      self._children.append(value)
  
  crossPropagationIntegrator = property(_getCrossPropagationIntegrator, _setCrossPropagationIntegrator)
  del _getCrossPropagationIntegrator, _setCrossPropagationIntegrator
  
  def reducedDimensionFieldForField(self, fullField):
    if fullField in self.fieldMap:
      return self.fieldMap[fullField]
    
    fieldsWithSameDimensions = filter(lambda x: fullField.dimensions == x.dimensions, self.fieldMap.values())
    if fieldsWithSameDimensions:
      result = fieldsWithSameDimensions[0]
      self.fieldMap[fullField] = result
      return result
    
    reducedField = FieldElement(name = 'cross_%s_%s' % (self.propagationDimension, fullField.name),
                                **self.argumentsToTemplateConstructors)
    reducedField.dimensions = filter(lambda x: x.name != self.propagationDimension, fullField.dimensions)
    
    self.fieldMap[fullField] = reducedField
    
    return reducedField
  
  def reducedDimensionVectorForVector(self, fullVector):
    if fullVector in self.dependencyMap:
      return self.dependencyMap[fullVector]
    if fullVector in self.integrationVectorMap:
      return self.integrationVectorMap[fullVector]
    
    # We have to create the vector element
    reducedField = self.reducedDimensionFieldForField(fullVector.field)
    
    vectorsWithSameName = filter(lambda v: v.name == fullVector.name, reducedField.vectors)
    if vectorsWithSameName:
      reducedVector = vectorsWithSameName[0]
    else:
      reducedVector = VectorElement(name = fullVector.name, field = reducedField,
                                    **self.argumentsToTemplateConstructors)
      
      reducedVector.type = fullVector.type
      reducedVector.components = fullVector.components
      reducedVector.needsInitialisation = False
      reducedField.temporaryVectors.add(reducedVector)
      self._children.append(reducedVector)
    
    return reducedVector
  
  def bindNamedVectors(self):
    super(_CrossPropagationOperator, self).bindNamedVectors()
    
    # Our named dependencies will already have been taken care of thanks to _Operator.bindNamedVectors()
    for vector in self.dependencies:
      reducedVector = self.reducedDimensionVectorForVector(vector)
      self.dependencyMap[vector] = reducedVector
    
    reducedDependencies = set(self.dependencyMap.values())
    # Add the reduced dependencies to the various parts of the cross-propagation integrator
    self.crossPropagationIntegrator.dependencies.update(reducedDependencies)
    self.crossPropagationIntegratorDeltaAOperator.dependencies.update(reducedDependencies)
    
    if self.integrationVectorsEntity:
      self.integrationVectors = self.vectorsFromEntity(self.integrationVectorsEntity)
      
      for integrationVector in self.integrationVectors:
        if not integrationVector.field == self.field:
          raise ParserException(self.integrationVectorsEntity.xmlElement, 
                                "Cannot integrate vector '%s' in this cross-propagation element as it "
                                "does not belong to the '%s' field." % (integrationVector.name, self.field.name))
        
        if integrationVector in self.parent.deltaAOperator.integrationVectors:
          raise ParserException(self.integrationVectorsEntity.xmlElement,
                                "Cannot integrate vector '%s' in this cross-propagation element as it "
                                "is being integrated by the ancestor integrator." % integrationVector.name)
        
        reducedVector = self.reducedDimensionVectorForVector(integrationVector)
        self.integrationVectorMap[integrationVector] = reducedVector
      
      # Add the reduced integration vectors to the various parts of the cross-propagation integrator
      reducedIntegrationVectors = set(self.integrationVectorMap.values())
      self.crossPropagationIntegrator.integrationVectors.update(reducedIntegrationVectors)
      self.crossPropagationIntegratorDeltaAOperator.integrationVectors.update(reducedIntegrationVectors)
      self.crossPropagationIntegratorDeltaAOperator.dependencies.update(reducedIntegrationVectors)
      
      self.parent.dependencies.update(self.integrationVectors)
    
    if self.boundaryConditionDependenciesEntity:
      self.boundaryConditionDependencies = self.vectorsFromEntity(self.boundaryConditionDependenciesEntity)
      
      for vector in self.boundaryConditionDependencies:
        if vector.field.hasDimensionName(self.propagationDimension):
          raise ParserException(self.boundaryConditionDependenciesEntity.xmlElement,
                                "Cannot depend on vector '%s' because it is in the field '%s'\n"
                                "which contains the cross-propagation dimension: '%s'."
                                % (vector.name, vector.field.name, self.propagationDimension))
        if not vector.field.isSubsetOfField(self.field):
          raise ParserException(self.boundaryConditionDependenciesEntity.xmlElement,
                                "Cannot depend on vector '%s' because it is in the field '%s'\n"
                                "which contains dimensions that are not in the field for this operator ('%s')."
                                % (vector.name, vector.field.name, self.field))
    
  
  def preflight(self):
    super(_CrossPropagationOperator, self).preflight()
    
    # Check that we aren't distributed with MPI along our intended integration dimension
    driver = self.getVar('features')['Driver']
    if self.propagationDimension in driver.distributedDimensionNames:
      raise ParserException(self.xmlElement, "Cannot cross-propagate along a dimension distributed with MPI.")
    
    # Create the dependency map and integration vector map for the cross propagation integrator
    # Note that they are reversed as they are reducedVector --> fullVector maps, not
    # fullVector --> reducedVector maps as we constructed above.
    
    self.crossPropagationIntegrator.dependencyMap = \
      dict([(reducedVector, fullVector) for (fullVector, reducedVector) in self.dependencyMap.iteritems()])
    self.crossPropagationIntegrator.integrationVectorMap = \
      dict([(reducedVector, fullVector) for (fullVector, reducedVector) in self.integrationVectorMap.iteritems()])
    
    # Copy the evolution code to the delta a operator
    self.crossPropagationIntegratorDeltaAOperator.propagationCode = self.operatorDefinitionCode
  
  

