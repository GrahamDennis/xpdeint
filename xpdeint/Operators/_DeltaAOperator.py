#!/usr/bin/env python
# encoding: utf-8
"""
_DeltaAOperator.py

Created by Graham Dennis on 2008-01-01.

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
from xpdeint.Vectors.VectorInitialisation import VectorInitialisation
from xpdeint.Function import Function
from xpdeint.Utilities import lazy_property

from xpdeint.ParserException import ParserException

from xpdeint import CodeParser

class _DeltaAOperator (Operator):
  evaluateOperatorFunctionArguments = [('real', '_step')]
  operatorKind = Operator.DeltaAOperatorKind
  
  def __init__(self, *args, **KWs):
    Operator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.integrationVectorsEntity = None
    self.integrationVectors = set()
    self.deltaAField = None
    self.deltaAVectorMap = {}
  
  @lazy_property
  def integrator(self):
    # Our parent is an OperatorContainer, and its parent is the Integrator
    return self.parent.parent
  
  def bindNamedVectors(self):
    super(_DeltaAOperator, self).bindNamedVectors()
    
    if self.integrationVectorsEntity:
      self.integrationVectors.update(self.vectorsFromEntity(self.integrationVectorsEntity))
      
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
        
        # Check that the user code block contains derivatives for every vector.
        # If not, throw an exception.
        
        if not derivativeString in self.primaryCodeBlock.codeString:
          raise ParserException(
            self.primaryCodeBlock.xmlElement,
            "Missing derivative for integration variable '%s' in vector '%s'." % (componentName, integrationVector.name)
          )
    
    
    
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
    
    dimRepNamesNeedingReordering = set()
    
    # Not all integration vectors may be forcing this reordering. For any that aren't,
    # we can just do the normal behaviour. This saves memory.
    self.vectorsForcingReordering = set()
    
    components = set()
    derivativeMap = {}
    propagationDimension = self.propagationDimension
    basis = self.primaryCodeBlock.basis
    dimRepNameMap = dict([(dimRep.name, dimRep) for dimRep in self.field.inBasis(basis)])
    
    for vector in self.integrationVectors:
      components.update(vector.components)
      for componentName in vector.components:
        derivativeString = ''.join(['d', componentName, '_d', propagationDimension])
        components.add(derivativeString)
        derivativeMap[derivativeString] = vector
    
    indexAccessedVariables = CodeParser.nonlocalDimensionAccessForComponents(components, self.primaryCodeBlock)
    
    simulationDriver = self.getVar('features')['Driver']
    
    for componentName, resultDict, codeSlice in indexAccessedVariables:
      
      vectors = [v for v in self.integrationVectors if componentName in v.components]
      
      if len(vectors) == 1:
        # Either our component belongs to one of the integration vectors
        vector = vectors[0]
      else:
        # Or it is a derivative, and so the vector we should use is the one for the original component
        vector = derivativeMap[componentName]
      
      # Add the dimension names that aren't being accessed with the dimension variable
      # to the set of dimensions needing reordering.
      dimRepNamesForThisVectorNeedingReordering = [dimRepName for dimRepName, (indexString, accessLoc) in resultDict.iteritems() if indexString != dimRepName]
      
      if vector.field.isDistributed:
        distributedDimRepsNeedingReordering = set(
          [dimRep.name for dimRep in self.field.inBasis(basis)
                  if dimRep.hasLocalOffset]
        ).intersection(dimRepNamesForThisVectorNeedingReordering)
        if distributedDimRepsNeedingReordering:
          # This vector is being accessed nonlocally on a dimension that is distributed. This isn't legal.
          dimRepName = list(distributedDimRepsNeedingReordering)[0]
          raise ParserException(self.xmlElement, 
                                  "The dimension '%(dimRepName)s' cannot be accessed nonlocally because it is being distributed with MPI. "
                                  "Try turning off MPI or re-ordering the dimensions in the <geometry> element." % locals())
      
      if dimRepNamesForThisVectorNeedingReordering:
        # If we have any dimensions that need reordering for this vector, add them to the complete set
        dimRepNamesNeedingReordering.update(dimRepNamesForThisVectorNeedingReordering)
        # ... and add the vector itself to the set of vectors forcing this reordering.
        self.vectorsForcingReordering.add(vector)
        
    
    
    # We now have all of the dimension names that need re-ordering to the end of the array.
    # We only need to do our magic if this set is non-empty
    if dimRepNamesNeedingReordering:
      
      # Now we need to construct a new field which has the same dimensions as self.field,
      # but has the dimensions that need reordering at the end.
      newFieldDimensions = self.field.dimensions[:]
      
      dimensionsNeedingReordering = []
      
      # Remove the dimensions needing reordering and replace them at the end
      for dim in newFieldDimensions[:]:
        if dim.inBasis(basis).name in dimRepNamesNeedingReordering:
          newFieldDimensions.remove(dim)
          newFieldDimensions.append(dim)
          dimensionsNeedingReordering.append(dim)
      
      loopingFieldName = ''.join([self.integrator.name, '_', self.name, '_looping_field'])
      
      loopingField = FieldElement(name = loopingFieldName,
                                  **self.argumentsToTemplateConstructors)
      
      loopingField.dimensions = [dim.copy(parent=loopingField) for dim in newFieldDimensions]
      self.primaryCodeBlock.field = loopingField
      
      # Now construct a second field for the vector which will hold our delta a operators
      deltaAFieldName = ''.join([self.integrator.name, '_', self.name, '_delta_a_field'])
      
      self.deltaAField = FieldElement(name = deltaAFieldName,
                                      **self.argumentsToTemplateConstructors)
      
      self.deltaAField.dimensions = [dim.copy(parent = self.deltaAField) for dim in dimensionsNeedingReordering]
      
      propagationDimension = self.propagationDimension
      
      # For each integration vector forcing the reordering, we need to construct
      # a corresponding vector in the new field.
      for integrationVector in self.vectorsForcingReordering:
        deltaAVector = VectorElement(
          name = integrationVector.name, field = self.deltaAField,
          parent = self, initialBasis = self.operatorBasis,
          type = integrationVector.type,
          **self.argumentsToTemplateConstructors
        )
        
        # The vector will only need initialisation if the derivatives are accessed out
        # of order, i.e. dphi_dt[j+1] for example. We can detect this later and change this
        # if that is the case.
        deltaAVector.needsInitialisation = False
        # Construct dx_dt variables for the delta a vector.
        deltaAVector.components = [''.join(['d', componentName, '_d', propagationDimension]) for componentName in integrationVector.components]
        
        # Make sure the vector gets allocated etc.
        self._children.append(deltaAVector)
        
        # Make the vector available when looping
        self.primaryCodeBlock.dependencies.add(deltaAVector)
        
        # Remove the components of the vector from our operatorComponents so that we won't get doubly-defined variables
        for componentName in deltaAVector.components:
          del self.operatorComponents[componentName]
        
        # Add the new delta a vector to the integration vector --> delta a vector map
        self.deltaAVectorMap[integrationVector] = deltaAVector
      
    
    # We need to rewrite all the derivatives to only use dimensions in the delta a field (if we have one)
    # This needs to be done even if we don't have a delta-a field as otherwise writing dx_dt(j: j) wouldn't
    # get transformed as dx_dt won't be vector.
    indexAccessedDerivatives = CodeParser.nonlocalDimensionAccessForComponents(derivativeMap.keys(), self.primaryCodeBlock)
    
    for componentName, resultDict, codeSlice in reversed(indexAccessedDerivatives):
      componentAccessString = componentName
      componentAccesses = []
      for dimRepName, (accessString, accessCodeLoc) in resultDict.iteritems():
        if not dimRepName in dimRepNamesNeedingReordering:
          continue
        componentAccesses.append('%(dimRepName)s => %(accessString)s' % locals())
      if componentAccesses:
        componentAccessString += '(' + ','.join(componentAccesses) + ')'
      
      # If we have at least one dimension that is not being accessed with the correct index,
      # we must initialise the delta a vector just in case. (See gravity.xmds for an example)
      if any([resultDict[dimRepName][0] != dimRepName for dimRepName in resultDict if dimRepName in dimRepNamesNeedingReordering]):
        # The integrationVector must be in the deltaAVectorMap because we would have had to allocate
        # a delta-a vector for this integration vector.
        deltaAVector = self.deltaAVectorMap[integrationVector]
        if not deltaAVector.needsInitialisation:
          deltaAVector.needsInitialisation = True
          deltaAVector.initialiser = VectorInitialisation(parent = deltaAVector, **self.argumentsToTemplateConstructors)
          deltaAVector.initialiser.vector = deltaAVector
      
      self.primaryCodeBlock.codeString = self.primaryCodeBlock.codeString[:codeSlice.start] + componentAccessString \
                                        + self.primaryCodeBlock.codeString[codeSlice.stop:]
      
    if self.deltaAField:
      copyDeltaAFunctionName = ''.join(['_', self.id, '_copy_delta_a'])
      loopingField = self.primaryCodeBlock.field
      arguments = [('real', '_step')]
      deltaAFieldReps = self.deltaAField.inBasis(self.operatorBasis)
      arguments.extend([('long', '_' + dimRep.name + '_index') \
                            for dimRep in loopingField.inBasis(self.operatorBasis) if not dimRep in deltaAFieldReps])
      copyDeltaAFunction = Function(name = copyDeltaAFunctionName,
                                    args = arguments,
                                    implementation = self.copyDeltaAFunctionContents,
                                    returnType = 'inline void')
      self.functions['copyDeltaA'] = copyDeltaAFunction
      
      # Create arguments dictionary for a call to the copyDeltaA function
      arguments = dict([('_' + dimRep.name + '_index', dimRep.loopIndex) \
                          for dimRep in loopingField.inBasis(self.operatorBasis) if not dimRep in deltaAFieldReps])
      functionCall = self.functions['copyDeltaA'].call(parentFunction = self.functions['evaluate'], arguments = arguments) + '\n'
      self.primaryCodeBlock.loopArguments['postDimensionLoopClosingCode'] = {
        self.deltaAField.dimensions[0].inBasis(self.operatorBasis).name: functionCall
      }
      
    
  
  

