#!/usr/bin/env python
# encoding: utf-8
"""
_DeltaAOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.Operator import Operator
from xpdeint.Geometry.FieldElement import FieldElement
from xpdeint.Vectors.VectorElement import VectorElement
from xpdeint.Vectors.VectorInitialisation import VectorInitialisation
from xpdeint.Function import Function

from xpdeint.ParserException import ParserException

import re
from xpdeint import RegularExpressionStrings

class _DeltaAOperator (Operator):
  evaluateOperatorFunctionArguments = [('double', '_step')]
  operatorKind = Operator.DeltaAOperatorKind
  
  def __init__(self, *args, **KWs):
    Operator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.integrationVectorsEntity = None
    self.integrationVectors = set()
    self.deltaAField = None
    self.deltaAVectorMap = {}
    self._propagationCode = None
    
  
  @property
  def defaultOperatorSpace(self):
    return 0
  
  @property
  def integrator(self):
    # Our parent is an OperatorContainer, and its parent is the Integrator
    return self.parent.parent
  
  def _getPropagationCode(self):
    if self._propagationCode:
      return self._propagationCode
    else:
      return self.insertUserCodeFromEntity(self.propagationCodeEntity)
  
  def _setPropagationCode(self, value):
    self._propagationCode = value
  
  # Create a propagationCode variable so that the propagation code can be overridden
  propagationCode = property(_getPropagationCode, _setPropagationCode)
  del _getPropagationCode, _setPropagationCode
  
  
  def bindNamedVectors(self):
    super(_DeltaAOperator, self).bindNamedVectors()
    
    if self.integrationVectorsEntity:
      self.integrationVectors = self.vectorsFromEntity(self.integrationVectorsEntity)
      
      for integrationVector in self.integrationVectors:
        if not integrationVector.field == self.field:
          raise ParserException(self.integrationVectorsEntity.xmlElement, 
                                "Cannot integrate vector '%s' in this operators element as it "
                                "belongs to a different field" % integrationVector.name)
        
      self.dependencies.update(self.integrationVectors)
  
  
  def preflight(self):
    super(_DeltaAOperator, self).preflight()
    
    # Construct the operator components dictionary
    for integrationVector in self.integrationVectors:
      for componentName in integrationVector.components:
        derivativeString = "d%s_d%s" % (componentName, self.propagationDimension)
        
        # Map of operator names to vector -> component list dictionary
        self.operatorComponents[derivativeString] = {integrationVector: [componentName]}
        
    
    if self.field.integerValuedDimensions:
      # Our job here is to consider the case where the user's integration code
      # depends on a component of an integration vector which might get overwritten
      # in the process of looping over the integration code. For example, if the
      # user has code like:
      # dx_dt[j] = x[j-1]
      # then on the previous loop, x[j-1] will have been overwritten with
      # dx_dt[j-1]*_step (due to the way the delta a operator works). Consequently,
      # x[j-1] won't mean what the user think it means. This would be OK if the code
      # was
      # dx_dt[j] = x[j + 1]
      # however we cannot safely know in all cases if j + 1 is greater than j or not.
      #
      # The solution will be to create an array to save all of the results for dx_dt
      # and then copy the results back in to the x array.
      #
      # As an optimisation, we don't want to do this if all of the accesses for an
      # integer valued dimension is with just the value of the dimension index.
      # 
      # Additionally, if we have an integer-valued dimension at the start that we
      # need to fix this problem for, the array would need to be large enough to
      # hold all of the dimensions after that dimension as well. To reduce the
      # memory requirement for this, we will re-order the looping of the dimensions
      # to put any integer-valued dimensions that need this special treatment as the
      # innermost loops.
      
      dimensionNamesNeedingReordering = set()
      
      # Not all integration vectors may be forcing this reordering. For any that aren't,
      # we can just do the normal behaviour. This saves memory.
      self.vectorsForcingReordering = set()
      
      components = set()
      derivativeMap = {}
      propagationDimension = self.propagationDimension
      
      for vector in self.integrationVectors:
        components.update(vector.components)
        for componentName in vector.components:
          derivativeString = ''.join(['d', componentName, '_d', propagationDimension])
          components.add(derivativeString)
          derivativeMap[derivativeString] = vector
      
      
      # The following regular expression has both a 'good' group and a 'bad' group
      # because we don't care about anything that might match an expression like
      # phi[j] if it happens to be inside another pair of square brackets, i.e.
      # something like L[phi[j]], as that will not be the same array.
      componentsWithIntegerValuedDimensionsRegex = \
        re.compile(r'(?P<bad>'  + RegularExpressionStrings.threeLevelsMatchedSquareBrackets + r')|'
                   r'(?P<good>' + RegularExpressionStrings.componentWithIntegerValuedDimensions(components) + ')',
                   re.VERBOSE)
      
      for match in componentsWithIntegerValuedDimensionsRegex.finditer(self.propagationCodeEntity.value):
        # If we have a match for the 'bad' group, ignore it
        if match.group('bad'):
          continue
        
        # So we now have a component, but if it doesn't have a match for 'integerValuedDimensions'
        # then we don't have to do anything with it.
        if not match.group('integerValuedDimensions'):
          continue
        
        componentName = match.group('componentName')
        vectors = [v for v in self.integrationVectors if componentName in v.components]
        
        if len(vectors) == 1:
          # Either our component belongs to one of the integration vectors
          vector = vectors[0]
        else:
          # Or it is a derivative, and so the vector we should use is the one for the original component
          vector = derivativeMap[componentName]
        
        regex = re.compile(RegularExpressionStrings.integerValuedDimensionsForComponentInField('', vector.field),
                           re.VERBOSE)
        
        integerValuedDimensionsMatch = regex.search(match.group('integerValuedDimensions'))
        
        if not integerValuedDimensionsMatch:
          target = match.group(0)
          raise ParserException(self.xmlElement,
                                "Unable to extract the integer-valued dimensions for the '%(componentName)s' variable.\n"
                                "The string that couldn't be parsed was '%(target)s'." % locals())
        
        integerValuedDimensions = vector.field.integerValuedDimensions
        
        integerValuedDimensionNames = []
        for dimList in integerValuedDimensions:
          integerValuedDimensionNames.extend([dim.name for dim in dimList])
        
        # Add the dimension names that aren't being accessed with the dimension variable
        # to the set of dimensions needing reordering.
        dimensionNamesForThisVectorNeedingReordering = [dimName for dimName in integerValuedDimensionNames if integerValuedDimensionsMatch.group(dimName).strip() != dimName]
        
        if dimensionNamesForThisVectorNeedingReordering:
          # If we have any dimensions that need reordering for this vector, add them to the complete set
          dimensionNamesNeedingReordering.update(dimensionNamesForThisVectorNeedingReordering)
          # ... and add the vector itself to the set of vectors forcing this reordering.
          self.vectorsForcingReordering.add(vector)
          
      
      
      # We now have all of the dimension names that need re-ordering to the end of the array.
      # We only need to do our magic if this set is non-empty
      if dimensionNamesNeedingReordering:
        # Turn the set of dimension names into a list of dimensions
        dimensionsNeedingReordering = [self.field.dimensionWithName(dimName) for dimName in dimensionNamesNeedingReordering]
        
        for dimension in dimensionsNeedingReordering:
          simulationDriver = self.getVar('features')['Driver']
          if dimension.name in simulationDriver.distributedDimensionNames:
            # If any of the dimensions needing reordering are distributed, then we simply can't do it as they will be accessed
            # nonlocally, and the user will probably be intending to access data that is stored on other ranks.
            dimensionName = dimension.name
            raise ParserException(self.xmlElement, 
                                    "The dimension '%(dimensionName)s' cannot be accessed nonlocally because it is being distributed with MPI.\n"
                                    "Try turning off MPI or re-ordering the dimensions in the <geometry> element." % locals())
        
        # Sort these dimensions in canonical order
        geometryTemplate = self.getVar('geometry')
        sortFunction = lambda x, y: cmp(geometryTemplate.indexOfDimension(x), geometryTemplate.indexOfDimension(y))
        dimensionsNeedingReordering.sort(sortFunction)
        
        # Now we need to construct a new field which has the same dimensions as self.field,
        # but has the dimensions that need reordering at the end.
        newFieldDimensions = self.field.dimensions[:]
        
        # First remove the dimensions needing reordering
        for dim in dimensionsNeedingReordering:
          newFieldDimensions.remove(dim)
        
        # Now put them at the end.
        newFieldDimensions.extend(dimensionsNeedingReordering)
        
        loopingFieldName = ''.join([self.integrator.name, '_', self.name, '_looping_field'])
        
        loopingField = FieldElement(name = loopingFieldName,
                                    **self.argumentsToTemplateConstructors)
        
        loopingField.dimensions = [dim.copy(parent=loopingField) for dim in newFieldDimensions]
        self.loopingField = loopingField
        
        # Now construct a second field for the vector which will hold our delta a operators
        deltaAFieldName = ''.join([self.integrator.name, '_', self.name, '_delta_a_field'])
        
        self.deltaAField = FieldElement(name = deltaAFieldName,
                                        **self.argumentsToTemplateConstructors)
        
        self.deltaAField.dimensions = [dim.copy(parent = self.deltaAField) for dim in dimensionsNeedingReordering]
        
        propagationDimension = self.propagationDimension
        
        # For each integration vector forcing the reordering, we need to construct
        # a corresponding vector in the new field.
        for integrationVector in self.vectorsForcingReordering:
          deltaAVector = VectorElement(name = integrationVector.name, field = self.deltaAField,
                                       **self.argumentsToTemplateConstructors)
          deltaAVector.type = integrationVector.type
          
          # The vector will only need initialisation if the derivatives are accessed out
          # of order, i.e. dphi_dt[j+1] for example. We can detect this later and change this
          # if that is the case.
          deltaAVector.needsInitialisation = False
          deltaAVector.initialSpace = self.operatorSpace
          # Construct dx_dt variables for the delta a vector.
          deltaAVector.components = [''.join(['d', componentName, '_d', propagationDimension]) for componentName in integrationVector.components]
          
          # Make sure the field knows about the vector
          self.deltaAField.temporaryVectors.add(deltaAVector)
          
          # Make sure the vector gets allocated etc.
          self._children.append(deltaAVector)
          
          # Make the vector available when looping
          self.dependencies.add(deltaAVector)
          
          # Remove the components of the vector from our operatorComponents so that we won't get doubly-defined variables
          for componentName in deltaAVector.components:
            del self.operatorComponents[componentName]
          
          # Add the new delta a vector to the integration vector --> delta a vector map
          self.deltaAVectorMap[integrationVector] = deltaAVector
      
      
      # We need to rewrite all the derivatives to only use dimensions in the delta a field (if we have one)
      deltaAIntegerValuedDimensions = []
      if self.deltaAField:
        deltaAIntegerValuedDimensions = self.deltaAField.integerValuedDimensions
      
      derivativesWithIntegerValuedDimensionsRegex = \
        re.compile(RegularExpressionStrings.componentWithIntegerValuedDimensions(derivativeMap.keys()),
                   re.VERBOSE)
      
      originalCode = self.propagationCodeEntity.value
      for match in derivativesWithIntegerValuedDimensionsRegex.finditer(originalCode):
        # If we don't have a match for integerValuedDimensions, then everything is OK
        if not match.group('integerValuedDimensions'):
          continue
        
        componentName = match.group('componentName')
        
        integrationVector = derivativeMap[componentName]
        
        regex = re.compile(RegularExpressionStrings.integerValuedDimensionsForComponentInField('', integrationVector.field),
                           re.VERBOSE)
        
        integerValuedDimensionsMatch = regex.search(match.group('integerValuedDimensions'))
        
        if not integerValuedDimensionsMatch:
          target = match.group(0)
          raise ParserException(self.xmlElement,
                                "Unable to extract the integer-valued dimensions for the '%(componentName)s' variable.\n"
                                "The string that couldn't be parsed was '%(target)s'." % locals())
        
        integerValuedDimensionsString = ''
        for dimList in deltaAIntegerValuedDimensions:
          integerValuedDimensionsString += '[' + ', '.join([integerValuedDimensionsMatch.group(dim.name) for dim in dimList]) + ']'
        
        # If we have at least one dimension that is not being accessed with the correct index,
        # we must initialise the delta a vector just in case. (See gravity.xmds for an example)
        if any([integerValuedDimensionsMatch.group(dim.name).strip() != dim.name for dim in dimList]):
          
          # The integrationVector must be in the deltaAVectorMap because we would have had to allocate
          # a delta-a vector for this integration vector.
          deltaAVector = self.deltaAVectorMap[integrationVector]
          if not deltaAVector.needsInitialisation:
            deltaAVector.needsInitialisation = True
            deltaAVector.initialiser = VectorInitialisation(**self.argumentsToTemplateConstructors)
            deltaAVector.initialiser.vector = deltaAVector
        
        # Replace the derivative string with one accessed using only indices corresponding to dimensions in
        # the delta a field.
        self.propagationCodeEntity.value = re.sub(re.escape(componentName) + re.escape(match.group('integerValuedDimensions')),
                                              componentName + integerValuedDimensionsString,
                                              self.propagationCodeEntity.value, count=1)
      
      
    
    if self.deltaAField:
      copyDeltaAFunctionName = ''.join(['_', self.id, '_copy_delta_a'])
      arguments = [('double', '_step')]
      arguments.extend([('long', '_' + dim.inSpace(self.operatorSpace).name + '_index') \
                            for dim in self.loopingField.dimensions if not self.deltaAField.hasDimension(dim)])
      copyDeltaAFunction = Function(name = copyDeltaAFunctionName,
                                    args = arguments,
                                    implementation = self.copyDeltaAFunctionContents,
                                    returnType = 'inline void')
      self.functions['copyDeltaA'] = copyDeltaAFunction
      
  

