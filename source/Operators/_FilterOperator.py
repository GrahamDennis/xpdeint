#!/usr/bin/env python
# encoding: utf-8
"""
_FilterOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from Operator import Operator
from FieldElement import FieldElement

import RegularExpressionStrings
from .ParserException import ParserException

class _FilterOperator (Operator):
  operatorKind = Operator.OtherOperatorKind
  vectorsMustBeInSubsetsOfIntegrationField = False
  
  @property
  def defaultOperatorSpace(self):
    return 0
  
  def preflight(self):
    super(_FilterOperator, self).preflight()
    
    dimensionNames = set()
    for dependency in self.dependencies:
      dimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    self.sourceField = FieldElement.sortedFieldWithDimensionNames(dimensionNames)
    
    if self.dependenciesEntity and self.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
       self.operatorSpace = self.sourceField.spaceFromString(self.dependenciesEntity.xmlElement.getAttribute('fourier_space'))
  
  


