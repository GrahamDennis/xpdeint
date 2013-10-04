#!/usr/bin/env python
# encoding: utf-8
"""
_IPOperator.py

Created by Graham Dennis on 2008-02-20.

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
from xpdeint.ParserException import ParserException, parserWarning

from xpdeint import CodeParser
from xpdeint.Utilities import lazy_property

class _IPOperator(Operator):
  evaluateOperatorFunctionArguments = [('int', '_exponent')]
  operatorKind = Operator.IPOperatorKind
  expFunction = 'exp'
  valueSuffix = ''
  
  @lazy_property
  def integrator(self):
    # Our parent is an OperatorContainer, and its parent is the Integrator
    return self.parent.parent
  
  def preflight(self):
    super(_IPOperator, self).preflight()
    
    for operatorName in self.operatorNames:
      self.operatorComponents[operatorName] = {}
    
    sharedCodeBlock = self.parent.sharedCodeBlock
    operatorTargetPairs = CodeParser.targetComponentsForOperatorsInString(self.operatorNames, sharedCodeBlock)
    
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
          indexAccessedVariables = CodeParser.nonlocalDimensionAccessForVectors(integrationVectors, sharedCodeBlock)
        
        try:
          # This will extract the componentName corresponding to the indexed variable in the target
          # or it will fail because it isn't of that form.
          componentName, resultDict = [(l[0], l[2]) for l in indexAccessedVariables if sharedCodeBlock.codeString[l[3]] == target][0]
        except IndexError:
          # Target didn't match something of the form 'phi[j, k][m+3,n-9]'
          raise ParserException(self.xmlElement,
                                "IP operators can only act on components of integration vectors. "
                                "The '%(operatorName)s' operator acting on '%(target)s' doesn't seem to be of the right form "
                                "or '%(target)s' isn't in one of the integration vectors."
                                % locals())
        
        # Check that nonlocally-accessed dimensions are being accessed with the dimension names
        # i.e. of the form 'phi(j: j, k:k, m:m, n:n)' not 'phi(j: j-7, k: k*2, m: 3, n: n+1)'
        for dimName, (indexString, codeSlice) in resultDict.iteritems():
          if not dimName == indexString:
            raise ParserException(self.xmlElement,
                                  "IP operators can only act on every value of a dimension. "
                                  "The problem was caused by the '%(operatorName)s' operator acting on '%(target)s'. "
                                  "EX operators do not have this restriction."
                                  % locals())
      
      if componentName in targetComponentNamesUsed:
        raise ParserException(self.xmlElement,
                              "Check the documentation, only one IP operator can act on a given component, "
                              "and this operator can only appear once. "
                              "The problem was with the '%(componentName)s' term appearing more than once in an IP operator. "
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
      
      if targetVector.type == 'real':
        self.operatorVector.type = 'real'
      
      
      # Check the sanity of the integration code.
      # i.e. check that we don't have something of the form:
      # dy_dt = L[x].
      # Obviously the user could hide this from us, but if we can check the most
      # common case that frequently goes wrong, then we should.
      
      CodeParser.performIPOperatorSanityCheck(componentName, self.propagationDimension, codeSlice, sharedCodeBlock)
      
      # Replace the L[x] string with 0.0
      sharedCodeBlock.codeString = sharedCodeBlock.codeString[:codeSlice.start] + '0.0' + sharedCodeBlock.codeString[codeSlice.stop:]
    
    
    # If any operator names weren't used in the code, issue a warning
    unusedOperatorNames = operatorNames.difference(operatorNamesUsed)
    if unusedOperatorNames:
      unusedOperatorNamesString = ', '.join(unusedOperatorNames)
      parserWarning(self.xmlElement,
                    "The following operator names weren't used: %(unusedOperatorNamesString)s" % locals())
    
    del self.functions['evaluate']
    vectors = set(self.targetVectors)
    self.registerVectorsRequiredInBasis(vectors, self.parent.ipOperatorBasis)
    
  


