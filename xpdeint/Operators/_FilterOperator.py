#!/usr/bin/env python
# encoding: utf-8
"""
_FilterOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.Operator import Operator
from xpdeint.Geometry.FieldElement import FieldElement

from xpdeint.Utilities import lazy_property

class _FilterOperator (Operator):
  # Filter operators must cause their computed vectors to be re-evaluated
  # as one filter operator could easily change the value of a computed vector
  # (think renormalisation)
  dynamicVectorsNeedingPrecalculation = []
  
  evaluateOperatorFunctionArguments = []
  operatorKind = Operator.OtherOperatorKind
  vectorsMustBeInSubsetsOfIntegrationField = False
  
  @lazy_property
  def field(self):
    return self.primaryCodeBlock.field
  
  def bindNamedVectors(self):
    super(_FilterOperator, self).bindNamedVectors()
    
    dimensionNames = set()
    for dependency in self.dependencies:
      dimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    codeBlock = self.primaryCodeBlock
    codeBlock.field = FieldElement.sortedFieldWithDimensionNames(dimensionNames)
    
    if codeBlock.dependenciesEntity and codeBlock.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
      codeBlock.basis = \
        codeBlock.field.basisFromString(
          codeBlock.dependenciesEntity.xmlElement.getAttribute('fourier_space'),
          xmlElement = codeBlock.dependenciesEntity.xmlElement
        )
    if not codeBlock.basis:
      codeBlock.basis = codeBlock.field.defaultCoordinateBasis
  


