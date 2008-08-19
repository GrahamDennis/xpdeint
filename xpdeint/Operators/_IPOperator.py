#!/usr/bin/env python
# encoding: utf-8
"""
_IPOperator.py

Created by Graham Dennis on 2008-02-20.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.Operator import Operator
from xpdeint.ParserException import ParserException, parserWarning

import re
from xpdeint import RegularExpressionStrings

class _IPOperator(Operator):
  evaluateOperatorFunctionArguments = [('int', '_exponent')]
  operatorKind = Operator.IPOperatorKind
  
  @property
  def integrator(self):
    # Our parent is an OperatorContainer, and its parent is the Integrator
    return self.parent.parent
  
  def preflight(self):
    super(Operator, self).preflight()
    
    operatorTargetPairs = self.targetComponentsForOperatorsInString(self.operatorNames, self.parent.sharedCode)
    
    if operatorTargetPairs:
      operatorNamesUsed = set()
      operatorNames = set(self.operatorNames)
      
      integrationVectors = self.parent.deltaAOperator.integrationVectors
      field = self.field
      
      legalTargetComponentNames = set()
      for v in integrationVectors:
        legalTargetComponentNames.update(v.components)
      
      targetComponentNamesUsed = set()
      
      targetRegex = re.compile(r'\s*' + RegularExpressionStrings.componentWithIntegerValuedDimensions(legalTargetComponentNames) + r'\s*$',
                               re.VERBOSE)
      
      
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
          raise ParserException(self.xmlElement,
                                "IP operators can only act on components of integration vectors.\n"
                                "The '%(operatorName)s' operator acting on '%(target)s' doesn't seem to be of the right form\n"
                                "or '%(target)s' isn't in one of the integration vectors."
                                % locals())
        
        componentName = match.group('componentName')
        if componentName in targetComponentNamesUsed:
          raise ParserException(self.xmlElement,
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
        
        # Now we have the vector, we can check that it doesn't have integer-valued dimensions specified
        # with values of anything other than the appropriate dimensions
        integerValuedDimensionsRegex = re.compile(r'\s*' + RegularExpressionStrings.integerValuedDimensionsForComponentInField(componentName, field) + r'\s*$',
                                                  re.VERBOSE)
        
        integerValuedDimensionsMatch = integerValuedDimensionsRegex.match(target)
        
        if integerValuedDimensionsMatch:
          # If we got a match, then we have integer-valued dimensions, and we need to check them.
          integerValuedDimensions = field.integerValuedDimensions
          for listOfIntegerValuedDimensions in integerValuedDimensions:
            if not match.group(dim.name).strip() == dim.name:
              raise ParserException(self.xmlElement,
                                    "IP operators can only act on every value of an integer-valued dimension.\n"
                                    "The problem was caused by the '%(operatorName)s' operator acting on '%(target)s'.\n"
                                    "EX operators do not have this restriction."
                                    % locals())
        
        # We have our match, now we need to create the operatorComponents dictionary
        if not operatorName in self.operatorComponents:
          self.operatorComponents[operatorName] = {targetVector: [componentName]}
        elif not targetVector in self.operatorComponents[operatorName]:
          self.operatorComponents[operatorName][targetVector] = [componentName]
        else:
          self.operatorComponents[operatorName][targetVector].append(componentName)
        
        if targetVector.type == 'double':
          self.operatorVector.type = 'double'
        
        # Regular expression to check the sanity of the integration code
        # i.e. to check that we don't have something of the form:
        # dy_dt = L[x].
        # Obviously the user could hide this from us, but if we can check the most
        # common case that frequently goes wrong, then we should.
        
        sanityRegex = re.compile(r'\bd(' + RegularExpressionStrings.symbol + r')_d' + re.escape(self.propagationDimension)
                                 + r'.*' + re.escape(operatorName) + r'\[' + re.escape(target) + r'\]')
        
        sanityResult = sanityRegex.findall(self.parent.sharedCode)
        
        assert len(sanityResult) <= 1
        
        if sanityResult:
          if sanityResult[0] != componentName:
            # If we had a match of the form dy_dt = L[x] we know there is a problem
            # Barf, and tell the user what to do to fix it
            derivativeVariable = sanityResult[0]
            propagationDimension = self.propagationDimension
            raise ParserException(self.xmlElement,
                                  "Due to the way IP operators work, they can only contribute\n"
                                  "to the derivative of the variable they act on,\n"
                                  "i.e. dx_dt = L[x] not dy_dt = L[x].\n\n"
                                  "What you probably need to use in this circumstance is an EX operator.\n"
                                  "The conflict was caused by:\n"
                                  "  d%(derivativeVariable)s_d%(propagationDimension)s = %(operatorName)s[%(componentName)s]\n"
                                  % locals())
        
        # Create a regular expression to replace the L[x] string with 0.0
        operatorCodeReplacementRegex = re.compile(r'\b' + re.escape(operatorName) + r'\[\s*' + re.escape(target) + r'\s*\]')
        
        replacementCode = operatorCodeReplacementRegex.sub('0.0', self.parent.sharedCode, count = 1)
        
        self.parent.sharedCode = replacementCode
      
      
      # If any operator names weren't used in the code, issue a warning
      unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
      if unusedOperatorNames:
        unusedOperatorNamesString = ', '.join(unusedOperatorNames)
        parserWarning(self.xmlElement,
                      "The following operator names weren't used: %(unusedOperatorNamesString)s" % locals())
      
    
  


