#!/usr/bin/env python
# encoding: utf-8
"""
_FilterOperator.py

Created by Graham Dennis on 2008-01-01.

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
    
    if codeBlock.dependenciesEntity and codeBlock.dependenciesEntity.xmlElement.hasAttribute('basis'):
      codeBlock.basis = \
        codeBlock.field.basisFromString(
          codeBlock.dependenciesEntity.xmlElement.getAttribute('basis'),
          xmlElement = codeBlock.dependenciesEntity.xmlElement
        )
    if not codeBlock.basis:
      codeBlock.basis = codeBlock.field.defaultCoordinateBasis
  


