#!/usr/bin/env python
# encoding: utf-8
"""
_IPOperator.py

Created by Graham Dennis on 2008-02-20.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.Operator import Operator
from xpdeint.ParserException import ParserException, parserWarning

from xpdeint import CodeLexer

class _IPOperator(Operator):
  evaluateOperatorFunctionArguments = [('int', '_exponent')]
  operatorKind = Operator.IPOperatorKind
  
  @property
  def integrator(self):
    # Our parent is an OperatorContainer, and its parent is the Integrator
    return self.parent.parent
  
  def preflight(self):
    super(Operator, self).preflight()
    
    for operatorName in self.operatorNames:
      self.operatorComponents[operatorName] = {}
    
    operatorTargetPairs = CodeLexer.targetComponentsForOperatorsInString(self.operatorNames, self.parent.sharedCodeEntity)
    
    operatorNamesUsed = set()
    operatorNames = set(self.operatorNames)
    
    integrationVectors = self.parent.deltaAOperator.integrationVectors
    field = self.field
    
    legalTargetComponentNames = set()
    for v in integrationVectors:
      legalTargetComponentNames.update(v.components)
    
    targetComponentNamesUsed = set()
    
    indexAccessedVariables = None
    
    # We loop over this in reverse order as we will be modifying the code string. So in order to not have to
    # re-run targetComponentsForOperatorsInString after each modification, we loop over the operatorTargetPairs in
    # reverse order so that slices (character index ranges) for earlier operator-target pairs don't change
    for operatorName, target, codeSlice in reversed(operatorTargetPairs):
      operatorNamesUsed.add(operatorName)
      
      # Target is what is inside the square brackets in the integration code block
      
      # As this is the IP operator, we have a few additional constraints
      # Firstly, the targets must be of the form 'phi' or 'phi[j,k][m,n]'
      # where j, k, m, n are the names of the integer dimension
      
      if target in legalTargetComponentNames:
        # Everything is OK
        componentName = target
      else:
        if indexAccessedVariables == None:
          indexAccessedVariables = CodeLexer.integerValuedDimensionsForVectors(integrationVectors, self.parent.sharedCodeEntity)
        
        try:
          # This will extract the componentName corresponding to the indexed variable in the target
          # or it will fail because it isn't of that form.
          componentName, resultDict = [(l[0], l[2]) for l in indexAccessedVariables if l[3] == codeSlice][0]
        except:
          # Target didn't match something of the form 'phi[j, k][m+3,n-9]'
          raise ParserException(self.xmlElement,
                                "IP operators can only act on components of integration vectors.\n"
                                "The '%(operatorName)s' operator acting on '%(target)s' doesn't seem to be of the right form\n"
                                "or '%(target)s' isn't in one of the integration vectors."
                                % locals())
        
        # Check that integer-valued dimensions are being accessed with the dimension names
        # i.e. of the form 'phi[j, k][m, n]' not 'phi[j-7, k*2][3, n+1]'
        for dimName, (indexString, codeSlice) in resultDict.iteritems():
          if not dimName == indexString:
            raise ParserException(self.xmlElement,
                                  "IP operators can only act on every value of an integer-valued dimension.\n"
                                  "The problem was caused by the '%(operatorName)s' operator acting on '%(target)s'.\n"
                                  "EX operators do not have this restriction."
                                  % locals())
      
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
      
      # We have our match, now we need to create the operatorComponents dictionary
      if not targetVector in self.operatorComponents[operatorName]:
        self.operatorComponents[operatorName][targetVector] = [componentName]
      else:
        self.operatorComponents[operatorName][targetVector].append(componentName)
      
      if targetVector.type == 'double':
        self.operatorVector.type = 'double'
      
      
      # Check the sanity of the integration code.
      # i.e. check that we don't have something of the form:
      # dy_dt = L[x].
      # Obviously the user could hide this from us, but if we can check the most
      # common case that frequently goes wrong, then we should.
      
      CodeLexer.performIPOperatorSanityCheck(componentName, self.propagationDimension, codeSlice, self.parent.sharedCodeEntity)
      
      # Replace the L[x] string with 0.0
      self.parent.sharedCode = self.parent.sharedCode[:codeSlice.start] + '0.0' + self.parent.sharedCode[codeSlice.stop:]
    
    
    # If any operator names weren't used in the code, issue a warning
    unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
    if unusedOperatorNames:
      unusedOperatorNamesString = ', '.join(unusedOperatorNames)
      parserWarning(self.xmlElement,
                    "The following operator names weren't used: %(unusedOperatorNamesString)s" % locals())
    
    
  


