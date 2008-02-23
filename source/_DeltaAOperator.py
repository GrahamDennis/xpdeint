#!/usr/bin/env python
# encoding: utf-8
"""
_DeltaAOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""


from Operator import Operator
from FieldElement import FieldElement
from VectorElement import VectorElement
from ParserException import ParserException

import re
import RegularExpressionStrings

class _DeltaAOperator (Operator):
  operatorKind = Operator.DeltaAOperatorKind
  def __init__(self, *args, **KWs):
    Operator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.integrationVectorsEntity = None
    self.integrationVectors = set()
    self.deltaAField = None
  
  @property
  def defaultOperatorSpace(self):
    return 0
  
  def bindNamedVectors(self):
    if self.integrationVectorsEntity:
      self.integrationVectors = self.vectorsFromEntity(self.integrationVectorsEntity)
      
      for integrationVector in self.integrationVectors:
        if not integrationVector.field == self.field:
          raise ParserException(self.integrationVectorsEntity.xmlElement, 
                                "Cannot integrate vector '%s' in this operators element as it "
                                "belongs to a different field" % integrationVector.name)
        
        for componentName in integrationVector.components:
          derivativeString = "d%s_d%s" % (componentName, self.getVar('propagationDimension'))
          
          # Map of operator names to vector -> component list dictionary
          self.operatorComponents[derivativeString] = {integrationVector: [componentName]}
          
      self.integrator.vectors.update(self.integrationVectors)
      self.dependencies.update(self.integrationVectors)
    
    super(_DeltaAOperator, self).bindNamedVectors()
    
  
  def preflight(self):
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
      
      # The following regular expression has both a 'good' group and a 'bad' group
      # because we don't care about anything that might match an expression like
      # phi[j] if it happens to be inside another pair of square brackets, i.e.
      # something like L[phi[j]], as that will not be the same array.
      componentsWithIntegerValuedDimensionsRegex = \
        re.compile(r'(?P<bad>'  + RegularExpressionStrings.threeLevelsMatchedSquareBrackets + r')|'
                   r'(?P<good>' + RegularExpressionStrings.componentWithIntegerValuedDimensions(self.integrationVectors) + ')',
                   re.VERBOSE)
      
      for match in componentsWithIntegerValuedDimensionsRegex.finditer(self.propagationCode):
        # If we have a match for the 'bad' group, ignore it
        if match.group('bad'):
          continue
        
        # So we now have a component, but if it doesn't have a match for 'integerValuedDimensions'
        # then we don't have to do anything with it.
        if not match.group('integerValuedDimensions'):
          continue
        
        componentName = match.group('componentName')
        vectors = [v for v in self.integrationVectors if componentName in v.components]
        assert len(vectors) == 1
        
        vector = vectors[0]
        regex = re.compile(RegularExpressionStrings.componentWithIntegerValuedDimensionsWithComponentAndVector('', vector),
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
                                    searchList = self.searchListTemplateArgument,
                                    filter = self.filterTemplateArgument)
        
        loopingField.dimensions = newFieldDimensions
        self.loopingField = loopingField
        
        # Now construct a second field for the vector which will hold our delta a operators
        deltaAFieldName = ''.join([self.integrator.name, '_', self.name, '_delta_a_field'])
        
        self.deltaAField = FieldElement(name = deltaAFieldName,
                                        searchList = self.searchListTemplateArgument,
                                        filter = self.filterTemplateArgument)
        
        self.deltaAField.dimensions = dimensionsNeedingReordering
        
        propagationDimension = self.getVar('propagationDimension')
        
        # For each integration vector forcing the reordering, we need to construct
        # a corresponding vector in the new field.
        for integrationVector in self.vectorsForcingReordering:
          deltaAVector = VectorElement(name = integrationVector.name, field = self.deltaAField,
                                       searchList = self.searchListTemplateArgument,
                                       filter = self.filterTemplateArgument)
          deltaAVector.needsFourierTransforms = False
          deltaAVector.type = integrationVector.type
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
    
    super(_DeltaAOperator, self).preflight()
  

