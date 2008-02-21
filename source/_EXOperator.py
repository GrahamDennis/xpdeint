#!/usr/bin/env python
# encoding: utf-8
"""
_EXOperator.py

Created by Graham Dennis on 2008-02-21.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from Operator import Operator
from ParserException import ParserException, parserWarning

import re
import RegularExpressionStrings

class _EXOperator(Operator):
  
  operatorKind = Operator.OtherOperatorKind
  
  def preflight(self):
    
    if hasattr(self, 'operatorComponentsEntity'):
      operatorTargetPairs = self.operatorComponentsEntity.value
      
      operatorNamesUsed = set()
      operatorNames = set(self.operatorNames)
      
      deltaADependencies = self.deltaAOperator.dependencies
      
      targetRegex = re.compile(RegularExpressionStrings.componentWithIntegerValuedDimensions(deltaADependencies),
                               re.VERBOSE)
      
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
          # FIXME: Make this work, don't barf
          raise ParserException(self.operatorComponentsEntity.xmlElement,
                                "At present, EX operators can only act on components of vectors.\n"
                                "This should be fixed in the future.\n"
                                "The '%(componentName)s' operator acting on '%(target)s' doesn't seem to be of the right form\n"
                                "or '%(target)s' isn't in one of the integration or dependency vectors."
                                % locals())
        else:
          componentName = match.group('componentName')
          
          # Now we need to get the vector corresponding to componentName
          tempVectorList = [v for v in deltaADependencies if componentName in v.components]
          assert len(tempVectorList) == 1
          targetVector = tempVectorList[0]
          
          # FIXME: This check is not necessarily correct.
          # If the operator space is the same as the vector's initialisation space and the space for the
          # deltaAOperator, then we don't need the vector to be of type complex
          
          # We need to check that the integration vector this component belongs to is complex
          if targetVector.type != 'complex':
            raise ParserException(self.operatorComponentsEntity.xmlElement,
                                  "Cannot act on vector '%s' because it is not of type complex." % targetVector.name)
          
          targetVector.needsFourierTransforms = True
          
          # We have our match, now we need to create the operatorComponents dictionary
          if not operatorName in self.operatorComponents:
            self.operatorComponents[operatorName] = {targetVector: [componentName]}
          elif not targetVector in self.operatorComponents[operatorName]:
            self.operatorComponents[operatorName][targetVector] = [componentName]
          else:
            self.operatorComponents[operatorName][targetVector].append(componentName)
          
          # Set the replacement string for the L[x] operator
          replacementString = "_%(operatorName)s_%(componentName)s" % locals()
          
          # Add the appropriate component to the result vector
          self.resultVector.components.append(replacementString)
          
          if match.group('integerValuedDimensions'):
            # The target of the operator was a string of the form:
            # L[phi[j-5, k*2][l, m % 9]]
            # As a result, we need to copy these things back in when making the replacement
            
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
