#!/usr/bin/env python
# encoding: utf-8
"""
_EXOperator.py

Created by Graham Dennis on 2008-02-21.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.Operator import Operator
from xpdeint.ParserException import ParserException, parserWarning
from xpdeint.ParsedEntity import ParsedEntity

from xpdeint.Vectors.ComputedVector import ComputedVector

import re
from xpdeint import RegularExpressionStrings

class _EXOperator(Operator):
  evaluateOperatorFunctionArguments = []
  
  operatorKind = Operator.OtherOperatorKind
  
  def preflight(self):
    super(Operator, self).preflight()
    
    operatorNamesUsed = set()
    operatorNames = set(self.operatorNames)
    
    operatorTargetPairs = self.targetComponentsForOperatorsInString(self.operatorNames, self.parent.sharedCode)
    
    if operatorTargetPairs:
      
      parentDependencies = self.parent.dependencies
      
      targetComponents = set()
      for vector in parentDependencies:
        targetComponents.update(vector.components)
      
      targetRegex = re.compile(r'\s*' + RegularExpressionStrings.componentWithIntegerValuedDimensions(targetComponents) + r'\s*$',
                               re.VERBOSE)
      
      specialTargetsVector = None
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
          
          if not specialTargetsVector:
            # Construct a filter operator to create the special targets vector
            specialTargetsVector = ComputedVector(name = self.id + "_special_targets", field = self.field,
                                                  xmlElement = self.xmlElement,
                                                  **self.argumentsToTemplateConstructors)
            
            self.field.temporaryVectors.add(specialTargetsVector)
            self._children.append(specialTargetsVector)
            self.dependencies.add(specialTargetsVector)
            
            # When constructing the 'special targets' vector it may depend on anything the parent code (usually delta a operator) depends on
            specialTargetsVector.dependencies = self.parent.dependencies.copy()
            
            # If all dependencies are of type double, then the special targets vector must be double too
            if all([v.type == 'double' for v in self.parent.dependencies]):
              specialTargetsVector.type = 'double'
            
            specialTargetsVector.evaluationSpace = self.parent.sharedCodeSpace
            specialTargetsVector.evaluationCodeEntity = ParsedEntity(None, '')
            specialTargetsVector.integratingComponents = False
            
            # We have to call preflight on the filter operator in case it has some preflight to do
            # as it won't be called by parser2.py
            specialTargetsVector.bindNamedVectors()
            specialTargetsVector.preflight()
          
          if not target in specialTargets:
            specialTargets.append(target)
            targetComponentName = 'target' + str(specialTargets.index(target))
            specialTargetsVector.components.append(targetComponentName)
            specialTargetsVector.evaluationCodeEntity.value += ''.join([targetComponentName, ' = ', target, ';\n'])
          
          targetComponentName = 'target' + str(specialTargets.index(target))
          targetVector = specialTargetsVector
        else:
          # We have a match for a component of a vector
          targetComponentName = match.group('componentName')
          
          # Now we need to get the vector corresponding to componentName
          tempVectorList = [v for v in parentDependencies if targetComponentName in v.components]
          assert len(tempVectorList) == 1
          targetVector = tempVectorList[0]
          
        # We have our match, now we need to create the operatorComponents dictionary
        if not operatorName in self.operatorComponents:
          self.operatorComponents[operatorName] = {}
        
        if not targetVector in self.operatorComponents[operatorName]:
          self.operatorComponents[operatorName][targetVector] = [targetComponentName]
        elif not targetComponentName in self.operatorComponents[operatorName][targetVector]:
          self.operatorComponents[operatorName][targetVector].append(targetComponentName)
        
        if targetVector.type == 'complex':
          for v in [self.operatorVector, self.resultVector]:
            if v:
              v.type = 'complex'
        
        # Set the replacement string for the L[x] operator
        replacementString = "_%(operatorName)s_%(targetComponentName)s" % locals()
          
        # Add the appropriate component to the result vector if it's not already there
        if not replacementString in self.resultVector.components:
          self.resultVector.components.append(replacementString)
        
        if match and match.group('integerValuedDimensions'):
          # The target of the operator was a string of the form:
          # L[phi[j-5, k*2][l, m % 9]]
          # As a result, we need to copy these things back in when making the replacement.
          # _ScriptElement.fixupComponentsWithIntegerValuedDimensions will handle the replacement
          # of the square brackets with something meaningful later.
          
          integerValuedDimensionsString = match.group('integerValuedDimensions')
          
          replacementString += integerValuedDimensionsString
        
        # Create a regular expression to replace the L[x] string with the appropriate string
        operatorCodeReplacementRegex = re.compile(r'\b' + re.escape(operatorName) + r'\[\s*' + re.escape(target) + r'\s*\]')
        
        replacementCode = operatorCodeReplacementRegex.sub(replacementString, self.parent.sharedCode, count = 1)
        
        self.parent.sharedCode = replacementCode
      
      
    # If any operator names weren't used in the code, issue a warning
    unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
    if unusedOperatorNames:
      unusedOperatorNamesString = ', '.join(unusedOperatorNames)
      raise ParserException(self.xmlElement,
                            "The following EX operator names were declared but not used: %(unusedOperatorNamesString)s" % locals())
    
    
    # Add the result vector to the shared dependencies for the operator container
    # These dependencies are just the delta a dependencies, so this is just adding
    # our result vector to the dependencies for the delta a operator
    if self.resultVector:
      self.parent.dependencies.add(self.resultVector)
    
    
  
