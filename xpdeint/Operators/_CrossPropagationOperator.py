#!/usr/bin/env python
# encoding: utf-8
"""
_CrossPropagationOperator.py

Created by Graham Dennis on 2008-03-01.

Copyright (c) 2008-2012, Graham Dennis

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

from xpdeint.Operators.Operator import Operator

from xpdeint.Geometry.FieldElement import FieldElement
from xpdeint.Vectors.VectorElement import VectorElement

from xpdeint.ParserException import ParserException
from xpdeint.Utilities import lazy_property

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
    self.integrationVectorsEntity = None
    self.integrationVectors = set()
    self.reducedVectorMap = {}
    self.fullVectorMap = {}
    self.integrationVectorMap = {}
    self.reducedField = None
  
  
  @lazy_property
  def fieldMap(self):
    """
    Return the field map for this cross-propagator.
    
    The fieldMap is a map from full fields to reduced cross-propagation fields that do not have the
    cross-propagation dimension. The fieldMap instances are shared between cross-propagators that have
    the same cross-propagation dimension.
    """
    if not self.propagationDimension in self.sharedFieldMap:
      self.sharedFieldMap[self.propagationDimension] = {}
    return self.sharedFieldMap[self.propagationDimension]
    
  
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
    if fullVector in self.reducedVectorMap:
      return self.reducedVectorMap[fullVector]
    # If the vector belongs to a field that lacks the cross-propagation field
    # then we can just use the original field and we don't need a reduced dimension
    # version of this vector.
    if not fullVector.field.hasDimensionName(self.propagationDimension):
      return fullVector
    
    # We have to create the vector element
    reducedField = self.reducedDimensionFieldForField(fullVector.field)
    
    vectorsWithSameName = filter(lambda v: v.name == fullVector.name, reducedField.vectors)
    if vectorsWithSameName:
      reducedVector = vectorsWithSameName[0]
    else:
      reducedVector = VectorElement(
        name = fullVector.name, field = reducedField,
        type = fullVector.type,
        **self.argumentsToTemplateConstructors
      )
      
      reducedVector.type = fullVector.type
      reducedVector.components = fullVector.components
      reducedVector.needsInitialisation = False
      reducedField.managedVectors.add(reducedVector)
    
    self.reducedVectorMap[fullVector] = reducedVector
    self.fullVectorMap[reducedVector] = fullVector
    
    return reducedVector
  
  def vectorForVectorName(self, vectorName, vectorDictionary):
    """
    This method allows us to override the mapping of vector names to vectors for our children.
    This way we can replace the full vectors specified by the user with their reduced equivalents.
    """
    # Don't try and remap vector names if we don't have a reduced vector map yet.
    # i.e. if we are parsing our own code blocks
    if not vectorName in vectorDictionary or not self.reducedVectorMap:
      return self.parent.vectorForVectorName(vectorName, vectorDictionary)
    return self.reducedDimensionVectorForVector(vectorDictionary[vectorName])
  
  def bindNamedVectors(self):
    super(_CrossPropagationOperator, self).bindNamedVectors()
    
    reducedDependencies = set()
    # Our named dependencies will already have been taken care of thanks to _Operator.bindNamedVectors()
    for vector in self.dependencies:
      reducedVector = self.reducedDimensionVectorForVector(vector)
      # If the reducedVector is the same as the vector, then it doesn't belong in the dependency map
      if not reducedVector == vector:
        reducedDependencies.add(reducedVector)
    
    # Add the reduced dependencies to the various parts of the cross-propagation integrator
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
      
      self.parent.sharedCodeBlock.dependencies.update(self.integrationVectors)
    
    
    boundaryConditionDependencies = self.codeBlocks['boundaryCondition'].dependencies
    boundaryConditionDependencies.update(self.integrationVectors)
    for vector in boundaryConditionDependencies:
      if not vector.field.isSubsetOfField(self.field):
        raise ParserException(self.codeBlocks['boundaryCondition'].xmlElement,
                              "Cannot depend on vector '%s' because it is in the field '%s' "
                              "which contains dimensions that are not in the field for this operator ('%s')."
                              % (vector.name, vector.field.name, self.field))
    
    if self.propagationDirection == '+':
      indexOverrideValue = '0'
    else:
      propDimRep = self.field.dimensionWithName(self.propagationDimension).inBasis(self.operatorBasis)
      indexOverrideValue = '(%s - 1)' % propDimRep.globalLattice
    indexOverrides = {self.propagationDimension: dict([(v.field, indexOverrideValue) for v in boundaryConditionDependencies])}
    self.codeBlocks['boundaryCondition'].loopArguments['indexOverrides'] = indexOverrides
  
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
      dict([(reducedVector, fullVector) for (fullVector, reducedVector) in self.reducedVectorMap.iteritems() if fullVector in self.dependencies])
    self.crossPropagationIntegrator.integrationVectorMap = \
      dict([(reducedVector, fullVector) for (fullVector, reducedVector) in self.integrationVectorMap.iteritems()])
    
    # Copy the evolution code to the delta a operator
    # self.crossPropagationIntegratorDeltaAOperator.codeBlocks['operatorDefinition'] = self.primaryCodeBlock
    
    # Allow the cross propagation dimension variable to exist in the delta a operator.
    self.crossPropagationIntegrator.functions['deltaA'].args.append(('real', self.propagationDimension)) # Add it to the calculate_delta_a function
    self.crossPropagationIntegratorDeltaAOperator.functions['evaluate'].args.append(('real', self.propagationDimension)) # Add it to the delta a operator
  
  

