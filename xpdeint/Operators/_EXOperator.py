#!/usr/bin/env python
# encoding: utf-8
"""
_EXOperator.py

Created by Graham Dennis on 2008-02-21.

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
from xpdeint.ParserException import parserWarning

from xpdeint import CodeParser

class _EXOperator(Operator):
  evaluateOperatorFunctionArguments = []
  
  operatorKind = Operator.OtherOperatorKind
  
  def preflight(self):
    super(_EXOperator, self).preflight()
    
    for operatorName in self.operatorNames:
      self.operatorComponents[operatorName] = {}
    
    operatorNamesUsed = set()
    operatorNames = set(self.operatorNames)
    sharedCodeBlock = self.parent.sharedCodeBlock
    
    operatorTargetPairs = CodeParser.targetComponentsForOperatorsInString(self.operatorNames, sharedCodeBlock)
    
    targetComponents = set()
    for vector in sharedCodeBlock.dependencies:
      targetComponents.update(vector.components)
    
    indexAccessedVariables = None
    
    # We loop over this in reverse order as we will be modifying the code string. So in order to not have to
    # re-run targetComponentsForOperatorsInString after each modification, we loop over the operatorTargetPairs in
    # reverse order so that slices (character index ranges) for earlier operator-target pairs don't change
    for operatorName, target, codeSlice in reversed(operatorTargetPairs):
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
        # We have direct access to the component, so just work out which vector it belongs to
        # Now we need to get the vector corresponding to componentName
        tempVectorList = [v for v in sharedCodeBlock.dependencies if targetComponentName in v.components]
        assert len(tempVectorList) == 1
        targetVector = tempVectorList[0]
      else:
        # The target of our EX operator isn't a simple component.
        # In principle, this could be OK. We just need to construct the variable using the result vector.
        # If the user has made a mistake with their code, the compiler will barf, not xpdeint. This isn't ideal
        # but we can't understand an arbitrary string; that's what the compiler is for.
        
        targetComponentName = sharedCodeBlock.addCodeStringToSpecialTargetsVector(target, codeSlice)
        targetVector = sharedCodeBlock.specialTargetsVector
      
      # We have our match, now we need to create the operatorComponents dictionary
      if not operatorName in self.operatorComponents:
        self.operatorComponents[operatorName] = {}
      
      if not targetVector in self.operatorComponents[operatorName]:
        self.operatorComponents[operatorName][targetVector] = [targetComponentName]
      elif not targetComponentName in self.operatorComponents[operatorName][targetVector]:
        self.operatorComponents[operatorName][targetVector].append(targetComponentName)
      
      if targetVector.type == 'complex':
        for v in [self.operatorVector, self.resultVector]:
          if v: v.type = 'complex'
      
      # Set the replacement string for the L[x] operator
      replacementString = "_%(operatorName)s_%(targetComponentName)s" % locals()
        
      
      sharedCodeBlock.codeString = sharedCodeBlock.codeString[:codeSlice.start] + replacementString + sharedCodeBlock.codeString[codeSlice.stop:]
    
    # If any operator names weren't used in the code, issue a warning
    unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
    if unusedOperatorNames:
      unusedOperatorNamesString = ', '.join(unusedOperatorNames)
      parserWarning(self.xmlElement,
                    "The following EX operator names were declared but not used: %(unusedOperatorNamesString)s" % locals())
    
    # Iterate over the operator components adding the appropriate bits to the resultVector, but do it in
    # the order of the components in the targetVectors to make it easier to optimise out an FFT.
    for operatorName, operatorDict in self.operatorComponents.iteritems():
      for targetVector, targetVectorUsedComponents in operatorDict.iteritems():
        for targetComponent in targetVector.components:
          if targetComponent in targetVectorUsedComponents:
            self.resultVector.components.append("_%(operatorName)s_%(targetComponent)s" % locals())
    
    if self.resultVector.nComponents == 0:
      self.resultVector.remove()
      self.resultVector = None
    
    # Add the result vector to the shared dependencies for the operator container
    # These dependencies are just the delta a dependencies, so this is just adding
    # our result vector to the dependencies for the delta a operator
    if self.resultVector:
      sharedCodeBlock.dependencies.add(self.resultVector)
    
    # If we are nonconstant then we need to add the target vectors to the dependencies of our primary code block
    if not 'calculateOperatorField' in self.functions:
      self.primaryCodeBlock.dependencies.update(self.targetVectors)
    
    vectors = set(self.targetVectors)
    vectors.add(self.resultVector)
    self.registerVectorsRequiredInBasis(vectors, self.operatorBasis)
    
