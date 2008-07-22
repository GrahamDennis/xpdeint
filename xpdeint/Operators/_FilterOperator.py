#!/usr/bin/env python
# encoding: utf-8
"""
_FilterOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.Operator import Operator
from xpdeint.Geometry.FieldElement import FieldElement

from xpdeint import RegularExpressionStrings
from xpdeint.ParserException import ParserException

class _FilterOperator (Operator):
  evaluateOperatorFunctionArguments = []
  operatorKind = Operator.OtherOperatorKind
  vectorsMustBeInSubsetsOfIntegrationField = False
  
  @property
  def defaultOperatorSpace(self):
    return 0
  
  @property
  def computedVectorsNeedingPrecalculation(self):
    return []
  
  
  def bindNamedVectors(self):
    super(_FilterOperator, self).bindNamedVectors()
    
    dimensionNames = set()
    for dependency in self.dependencies:
      dimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    self.field = FieldElement.sortedFieldWithDimensionNames(dimensionNames)
    
    if self.dependenciesEntity and self.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
       self.operatorSpace = self.field.spaceFromString(self.dependenciesEntity.xmlElement.getAttribute('fourier_space'),
                                                       xmlElement = self.dependenciesEntity.xmlElement)
  
  


