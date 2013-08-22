#!/usr/bin/env python
# encoding: utf-8
"""
_UniformDimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.

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

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation

class _UniformDimensionRepresentation(DimensionRepresentation):
  instanceAttributes = ['_minimum',  '_maximum', '_stepSize']
  
  @property
  def stepSizeString(self):
    if self._stepSize:
      return self._stepSize
    else:
      return '((%(maximum)s - %(minimum)s)/%(globalLattice)s)' % dict(
        minimum = self.minimum,
        maximum = self.maximum,
        globalLattice = self.globalLattice
      )
  
  def openLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.openLoopAscending()
    elif loopingOrder == self.LoopingOrder.StrictlyDescendingOrder:
      return self.openLoopDescending()
    else:
      raise NotImplemented
  
  def closeLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.closeLoopAscending()
    elif loopingOrder == self.LoopingOrder.StrictlyDescendingOrder:
      return self.closeLoopDescending()
    else:
      raise NotImplemented
  
  def nonlocalAccessIndexFromStringForFieldInBasis(self, accessString, field, basis):
    result = super(_UniformDimensionRepresentation, self).nonlocalAccessIndexFromStringForFieldInBasis(accessString, field, basis)
    if result: return result
    # We only support non-local access for integer-valued dimensions, or access to the minimum value
    minimum = self.minimum
    # We shouldn't be called if we are distributed, but let's check just to be safe.
    if self.hasLocalOffset: return
    
    if not self.type == 'long':
      if not self._stepSize and accessString == self._minimum:
        return '0'
      elif accessString == ('-' + self.name):
        canAccessNegativeVariable = False
        if self._minimum == ('-' + self._maximum):
          canAccessNegativeVariable = True
        elif 'Validation' in self.getVar('features'):
          canAccessNegativeVariable = True
          validationFeature = self.getVar('features')['Validation']
          validationFeature.validationChecks.append("""
          if (fabs(%(maximum)s + %(minimum)s) > 0.1 * %(stepSize)s)
            _LOG(_ERROR_LOG_LEVEL, "ERROR: Nonlocal access of dimension '%(dimRepName)s' using '-%(dimRepName)s' is only valid for dimensions symmetric about zero.\\n");\n""" % {'maximum': self.maximum, 'minimum': self.minimum, 'dimRepName': self.name, 'stepSize': self.stepSize})
        
        if canAccessNegativeVariable:
          lattice = self.globalLattice
          loopIndex = self.loopIndex
          return '(%(lattice)s - %(loopIndex)s) %% %(lattice)s' % locals()
      return
    return '(%(accessString)s) - %(minimum)s' % locals()
  

