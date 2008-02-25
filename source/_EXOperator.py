#!/usr/bin/env python
# encoding: utf-8
"""
_EXOperator.py

Created by Graham Dennis on 2008-02-21.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from Operator import Operator
from ParserException import ParserException, parserWarning

from VectorElement import VectorElement
from FilterOperator import FilterOperator

import re
import RegularExpressionStrings

class _EXOperator(Operator):
  
  operatorKind = Operator.OtherOperatorKind
  
  def preflight(self):
    
    if self.hasattr('operatorComponentsEntity'):
      operatorTargetPairs = self.operatorComponentsEntity.value
      
      operatorNamesUsed = set()
      operatorNames = set(self.operatorNames)
      
      deltaADependencies = self.deltaAOperator.dependencies
      
      deltaAComponents = set()
      for vector in deltaADependencies:
        deltaAComponents.update(vector.components)
      
      targetRegex = re.compile(r'\s*' + RegularExpressionStrings.componentWithIntegerValuedDimensions(deltaAComponents) + r'\s*$',
                               re.VERBOSE)
      
      specialTargetsFilter = None
      specialTargets = []
      
      for operatorName, target in operatorTargetPairs:
        operatorNamesUsed.add(operatorName)
        
        # Target is what is inside the square brackets in the integration code block
        target = target.strip()
        
        # As this is the EX operator, we have fewer constraints.
        # If the target matches something of the form 'phi' or 'phi[j+3, k*k][m % 3, n]'
        # Then we don't need to use our result vector to make 'phi' available to the operator
        # If it doesn't match, then we have to assume that the expression is well formed, and
        # copy it into the result vector then fourier transform it into the space of the operator
        
        # If the target string doesn't match the regular expression, then
        # we need to use the target string to construct variables in the result vector
        match = targetRegex.match(target)
        
        if not match:
          # In principle, this could be OK. We just need to construct the variable using the result vector.
          # If the user has made a mistake with their code, the compiler will barf, not xpdeint. This isn't ideal
          # but we can't understand an arbitrary string; that's what the compiler is for.
          
          if not specialTargetsFilter:
            # Construct a filter operator to create the special targets vector
            specialTargetsFilter = FilterOperator(field = self.field, integrator = self.integrator,
                                                  searchList = self.searchListTemplateArgument,
                                                  filter = self.filterTemplateArgument)
            specialTargetsFilter.xmlElement = self.xmlElement
            
            # Shift the filter operator to be before this operator
            self.integrator.operators.remove(specialTargetsFilter)
            self.integrator.operators.insert(self.integrator.operators.index(self), specialTargetsFilter)
            
            specialTargetsFilter.integratingMoments = False
            
            # When constructing the 'special targets' we may depend on anything the delta a operator depends on
            specialTargetsFilter.dependencies = self.deltaAOperator.dependencies
            
            specialTargetsFilter.sourceField = self.field
            specialTargetsFilter.operatorSpace = self.deltaAOperator.operatorSpace
            specialTargetsFilter.operatorDefinitionCode = ''
            
            specialTargetVector = VectorElement(name = self.id + '_special_targets', field = self.field,
                                                searchList = self.searchListTemplateArgument,
                                                filter = self.filterTemplateArgument)
            
            specialTargetVector.initialSpace = self.deltaAOperator.operatorSpace
            specialTargetVector.type = 'complex'
            specialTargetVector.needsInitialisation = False
            self.field.temporaryVectors.add(specialTargetVector)
            
            specialTargetsFilter.resultVector = specialTargetVector
            
            # We have to call preflight on the filter operator in case it has some preflight to do
            # as it won't be called by parser2.py
            specialTargetsFilter.preflight()
          
          if not target in specialTargets:
            specialTargets.append(target)
            targetComponentName = 'target' + str(specialTargets.index(target))
            specialTargetVector.components.append(targetComponentName)
            specialTargetsFilter.operatorDefinitionCode += ''.join([targetComponentName, ' = ', target, ';\n'])
            
          
          targetComponentName = 'target' + str(specialTargets.index(target))
          
          targetVector = specialTargetVector
        else:
          targetComponentName = match.group('componentName')
          
          # Now we need to get the vector corresponding to componentName
          tempVectorList = [v for v in deltaADependencies if targetComponentName in v.components]
          assert len(tempVectorList) == 1
          targetVector = tempVectorList[0]
          
        # We have our match, now we need to create the operatorComponents dictionary
        if not operatorName in self.operatorComponents:
          self.operatorComponents[operatorName] = {}
        
        if not targetVector in self.operatorComponents[operatorName]:
          self.operatorComponents[operatorName][targetVector] = [targetComponentName]
        else:
          self.operatorComponents[operatorName][targetVector].append(targetComponentName)
        
        # Set the replacement string for the L[x] operator
        replacementString = "_%(operatorName)s_%(targetComponentName)s" % locals()
          
        # Add the appropriate component to the result vector
        self.resultVector.components.append(replacementString)
        
        if match and match.group('integerValuedDimensions'):
          # The target of the operator was a string of the form:
          # L[phi[j-5, k*2][l, m % 9]]
          # As a result, we need to copy these things back in when making the replacement.
          # _ScriptElement.fixupComponentsWithIntegerValuedDimensions will handle the replacement
          # of the square brackets with something meaningful later.
          
          integerValuedDimensionsString = match.group('integerValuedDimensions')
          
          replacementString += integerValuedDimensionsString
        
        escape = RegularExpressionStrings.escapeStringForRegularExpression
        
        # Create a regular expression to replace the L[x] string with the appropriate string
        operatorCodeReplacementRegex = re.compile(r'\b' + escape(operatorName) + r'\[\s*' + escape(target) + r'\s*\]')
        
        replacementCode = operatorCodeReplacementRegex.sub(replacementString, self.deltaAOperator.propagationCode, count = 1)
        
        self.deltaAOperator.propagationCode = replacementCode
      
      
      # If any operator names weren't used in the code, issue a warning
      unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
      if unusedOperatorNames:
        unusedOperatorNamesString = ', '.join(unusedOperatorNames)
        parserWarning(self.operatorComponentsEntity.xmlElement,
                      "The following operator names weren't used: %(unusedOperatorNamesString)s" % locals())
      
    
    super(Operator, self).preflight()
