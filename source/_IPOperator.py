#!/usr/bin/env python
# encoding: utf-8
"""
_IPOperator.py

Created by Graham Dennis on 2008-02-20.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from Operator import Operator
from ParserException import ParserException, parserWarning

import re
import RegularExpressionStrings

class _IPOperator(Operator):
  
  operatorKind = Operator.IPOperatorKind
  
  def preflight(self):
    
    if self.hasattr('operatorComponentsEntity'):
      operatorTargetPairs = self.operatorComponentsEntity.value
      
      operatorNamesUsed = set()
      operatorNames = set(self.operatorNames)
      
      integrationVectors = self.deltaAOperator.integrationVectors
      field = self.field
      
      legalTargetComponentNames = set()
      for v in integrationVectors:
        legalTargetComponentNames.update(v.components)
      
      targetComponentNamesUsed = set()
      
      # FIXME: In order to reduce the number of regular expressions that need to be maintained,
      # this code should use RegularExpressionStrings.componentWithIntegerValuedDimensions
      # and RegularExpressionStrings.componentWithIntegerValuedDimensionsWithComponentAndVector
      
      integerValuedDimensionsRegexString = ''
      integerValuedDimensions = field.integerValuedDimensions
      for listOfIntegerValuedDimensions in integerValuedDimensions:
        integerValuedDimensionsRegexString += r'\[\s*' + r'\s*,\s*'.join([dim.name for dim in listOfIntegerValuedDimensions]) + r'\s*\]'
      
      # We need to construct a regular expression that the targets must match.
      # The expression is of the form:
      # (component1|component2)(?:\[\s*j\s*,\s*k\s*\])?
      # i.e. should match anything of the form
      # component1 or component2[ j, k ]
      targetRegex = re.compile('(?P<componentName>' + '|'.join(legalTargetComponentNames) + ')(?:' + integerValuedDimensionsRegexString + ')?')
      
      for operatorName, target in operatorTargetPairs:
        operatorNamesUsed.add(operatorName)
        
        # Target is what is inside the square brackets in the integration code block
        target = target.strip()
        
        # As this is the IP operator, we have a few additional constraints
        # Firstly, the targets must be of the form 'phi' or 'phi[j,k][m,n]'
        # where j, k, m, n are the names of the integer dimension
        
        # If the target string doesn't match the regular expression, then
        # the IP operator is invalid
        match = targetRegex.match(target)
        
        if not match:
          raise ParserException(self.operatorComponentsEntity.xmlElement,
                                "IP operators can only act on components of integration vectors.\n"
                                "The '%(componentName)s' operator acting on '%(target)s' doesn't seem to be of the right form\n"
                                "or '%(target)s' isn't in one of the integration vectors."
                                % locals())
        
        componentName = match.group('componentName')
        if componentName in targetComponentNamesUsed:
          raise ParserException(self.operatorComponentsEntity.xmlElement,
                                "Check the documentation, only one IP operator can act on a given component,\n"
                                "and this operator can only appear once.\n"
                                "The problem was with the '%(componentName)s' term appearing more than once in an IP operator.\n"
                                "You may be able to accomplish what you are trying with an EX operator."
                                % locals())
        
        targetComponentNamesUsed.add(componentName)
        
        # Now we need to get the vector corresponding to componentName
        tempVectorList = [v for v in integrationVectors if componentName in v.components]
        assert len(tempVectorList) == 1
        targetVector = tempVectorList[0]
        
        # FIXME: If the operator space is the same as the vector's initial space, then the
        # vector doesn't need to be complex, and we don't need fourier transforms
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
        
        # Regular expression to check the sanity of the integration code
        # i.e. to check that we don't have something of the form:
        # dy_dt = L[x].
        # Obviously the user could hide this from us, but if we can check the most
        # common case that frequently goes wrong, then we should.
        
        escape = RegularExpressionStrings.escapeStringForRegularExpression
        
        sanityRegex = re.compile(r'\bd(' + RegularExpressionStrings.symbol + r')_d' + escape(self.getVar('propagationDimension'))
                                 + r'.*' + escape(operatorName) + r'\[' + escape(target) + r'\]')
        
        sanityResult = sanityRegex.findall(self.deltaAOperator.propagationCode)
        
        assert len(sanityResult) <= 1
        
        if sanityResult:
          if sanityResult[0] != componentName:
            # If we had a match of the form dy_dt = L[x] we know there is a problem
            # Barf, and tell the user what to do to fix it
            derivativeVariable = sanityResult[0]
            propagationDimension = self.getVar('propagationDimension')
            raise ParserException(self.operatorComponentsEntity.xmlElement,
                                  "Due to the way IP operators work, they can only contribute\n"
                                  "to the derivative of the variable they act on,\n"
                                  "i.e. dx_dt = L[x] not dy_dt = L[x].\n\n"
                                  "What you probably need to use in this circumstance is an EX operator.\n"
                                  "The conflict was caused by:\n"
                                  "  d%(derivativeVariable)s_d%(propagationDimension)s = %(operatorName)s[%(componentName)s]\n"
                                  % locals())
        
        # Create a regular expression to replace the L[x] string with 0.0
        operatorCodeReplacementRegex = re.compile(r'\b' + escape(operatorName) + r'\[\s*' + escape(target) + r'\s*\]')
        
        replacementCode = operatorCodeReplacementRegex.sub('0.0', self.deltaAOperator.propagationCode, count = 1)
        
        self.deltaAOperator.propagationCode = replacementCode
      
      
      # If any operator names weren't used in the code, issue a warning
      unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
      if unusedOperatorNames:
        unusedOperatorNamesString = ', '.join(unusedOperatorNames)
        parserWarning(self.operatorComponentsEntity.xmlElement,
                      "The following operator names weren't used: %(unusedOperatorNamesString)s" % locals())
      
    
    super(Operator, self).preflight()
