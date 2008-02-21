#!/usr/bin/env python
# encoding: utf-8
"""
_DeltaAOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""


from Operator import Operator
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
    if self.getVar('geometry').integerValuedDimensions:
      # The following regular expression has both a 'good' group and a 'bad' group
      # because we don't want to touch anything that might match an expression like
      # phi[j] if it happens to be inside another pair of square brackets, i.e.
      # something like L[phi[j]], as that will be taken care of elsewhere.
      componentsWithIntegerValuedDimensionsRegex = \
        re.compile(r'(?P<bad>'  + RegularExpressionStrings.threeLevelsMatchedSquareBrackets + r')|'
                   r'(?P<good>' + RegularExpressionStrings.componentWithIntegerValuedDimensions(self.dependencies) + ')',
                   re.VERBOSE)
      
      originalCode = self.propagationCode
      
      for match in componentsWithIntegerValuedDimensionsRegex.finditer(originalCode):
        # If we have a match for the 'bad' group, ignore it
        if match.group('bad'):
          continue
        
        # So we now have a component, but if it doesn't have a match for 'integerValuedDimensions'
        # then we don't have to do anything with it.
        if not match.group('integerValuedDimensions'):
          continue
        
        componentName = match.group('componentName')
        vectors = [v for v in self.dependencies if componentName in v.components]
        assert len(vectors) == 1
        
        vector = vectors[0]
        regex = re.compile(RegularExpressionStrings.componentWithIntegerValuedDimensionsWithComponentAndVector(componentName, vector),
                           re.VERBOSE)
        
        integerValuedDimensionsMatch = regex.search(self.propagationCode)
        
        if not integerValuedDimensionsMatch:
          target = match.group(0)
          raise ParserException(self.xmlElement,
                                "Unable to extract the integer-valued dimensions for the '%(componentName)s' variable.\n"
                                "The string that couldn't be parsed was '%(target)s'." % locals())
        
        integerValuedDimensions = vector.field.integerValuedDimensions
        
        integerValuedDimensionNames = []
        for dimList in integerValuedDimensions:
          integerValuedDimensionNames.extend([dim.name for dim in dimList])
        
        argumentsString = ', '.join([integerValuedDimensionsMatch.group(dimName).strip() for dimName in integerValuedDimensionNames])
        
        replacementString = '_%(componentName)s(%(argumentsString)s)' % locals()
        
        escape = RegularExpressionStrings.escapeStringForRegularExpression
        
        # Create a regular expression to replace the phi[j] string with the appropriate string
        operatorCodeReplacementRegex = re.compile(r'\b' + escape(componentName) + escape(match.group('integerValuedDimensions')))
        
        self.propagationCode = operatorCodeReplacementRegex.sub(replacementString, self.propagationCode, count = 1)
    
    super(_DeltaAOperator, self).preflight()
  

