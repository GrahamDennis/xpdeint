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

from xpdeint import CodeLexer

class _EXOperator(Operator):
  evaluateOperatorFunctionArguments = []
  
  operatorKind = Operator.OtherOperatorKind
  
  def preflight(self):
    super(Operator, self).preflight()
    
    for operatorName in self.operatorNames:
      self.operatorComponents[operatorName] = {}
    
    operatorNamesUsed = set()
    operatorNames = set(self.operatorNames)
    
    operatorTargetPairs = CodeLexer.targetComponentsForOperatorsInString(self.operatorNames, self.parent.sharedCodeEntity)
    
    parentDependencies = self.parent.dependencies
    
    targetComponents = set()
    for vector in parentDependencies:
      targetComponents.update(vector.components)
    
    specialTargetsVector = None
    specialTargets = []
    
    indexAccessedVariables = None
    
    for operatorName, target, codeSlice in operatorTargetPairs:
      operatorNamesUsed.add(operatorName)
      
      # Target is what is inside the square brackets in the integration code block
      
      # As this is the EX operator, we have fewer constraints.
      # If the target matches something of the form 'phi' or 'phi[j+3, k*k][m % 3, n]'
      # Then we don't need to use our result vector to make 'phi' available to the operator
      # If it doesn't match, then we have to assume that the expression is well formed, and
      # copy it into the result vector then fourier transform it into the space of the operator
      targetVector = None
      replacementStringSuffix = ''
      
      if target in targetComponents:
        targetComponentName = target
      else:
        # The target might just be an indexed component i.e. phi[j+3, etc..]
        if indexAccessedVariables == None:
          indexAccessedVariables = CodeLexer.integerValuedDimensionsForVectors(parentDependencies, self.parent.sharedCodeEntity)
        
        try:
          # This will extract the componentName corresponding to the indexed variable access if it is of that form
          targetComponentName = [l[0] for l in indexAccessedVariables if l[3] == codeSlice][0]
        except:
          # The target of our EX operator isn't a simple component.
          # In principle, this could be OK. We just need to construct the variable using the result vector.
          # If the user has made a mistake with their code, the compiler will barf, not xpdeint. This isn't ideal
          # but we can't understand an arbitrary string; that's what the compiler is for.
          
          if not specialTargetsVector:
            # Construct a filter operator to create the special targets vector
            specialTargetsVector = ComputedVector(name = self.id + "_special_targets", field = self.field,
                                                  parent = self,
                                                  xmlElement = self.xmlElement,
                                                  **self.argumentsToTemplateConstructors)
            
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
          # We were able to extract the componentName corresponding to the index variable access
          replacementStringSuffix = self.parent.sharedCode[codeSlice]
          assert replacementStringSuffix.startswith(targetComponentName)
          replacementStringSuffix = replacementStringSuffix[len(targetComponentName):]
          
      if not targetVector:
        # We have direct access to the component, so just work out which vector it belongs to
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
      
      if replacementStringSuffix:
        replacementString += replacementStringSuffix
      
      self.parent.sharedCode = self.parent.sharedCode[:codeSlice.start] + replacementString + self.parent.sharedCode[codeSlice.stop:]
    
    
    # If any operator names weren't used in the code, issue a warning
    unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
    if unusedOperatorNames:
      unusedOperatorNamesString = ', '.join(unusedOperatorNames)
      parserWarning(self.xmlElement,
                    "The following EX operator names were declared but not used: %(unusedOperatorNamesString)s" % locals())
    
    if self.resultVector.nComponents == 0:
      self.resultVector.remove()
      self.resultVector = None
    
    # Add the result vector to the shared dependencies for the operator container
    # These dependencies are just the delta a dependencies, so this is just adding
    # our result vector to the dependencies for the delta a operator
    if self.resultVector:
      self.parent.dependencies.add(self.resultVector)
    
    
  
