#!/usr/bin/env python
# encoding: utf-8
"""
_BreakpointSegment.py

Created by Graham Dennis on 2008-03-15.

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

from xpdeint.Segments._Segment import _Segment
from xpdeint.ParserException import ParserException

from xpdeint.Utilities import lazy_property

class _BreakpointSegment (_Segment):
  def __init__(self, *args, **KWs):
    _Segment.__init__(self, *args, **KWs)
    
    self.filename = None
    self.field = None
    self.outputGroups = 1
  
  @lazy_property
  def outputComponents(self):
    result = []
    for vector in self.orderedDependencies:
      for componentName in vector.components:
        result.append(componentName + 'R')
        if vector.type == 'complex':
          result.append(componentName + 'I')
    return result
  
  def bindNamedVectors(self):
    super(_Segment, self).bindNamedVectors()
    
    aVector = list(self.dependencies)[0]
    for vector in self.dependencies:
      if not vector.field.dimensions == aVector.field.dimensions:
        raise ParserException(self.xmlElement, "All vectors for a breakpoint element must be have the same dimensions.\n"
                                               "The conflicting vectors are: '%s' and '%s'." % (vector.name, aVector.name))
    self.field = aVector.field
    # We rely on a constant order for our dependencies when writing out
    self.orderedDependencies = list(self.dependencies)
  
  def preflight(self):
    super(_Segment, self).preflight()
    
    if self.dependenciesEntity.xmlElement.hasAttribute('basis'):
      spaceString = self.dependenciesEntity.xmlElement.getAttribute('basis')
      self.breakpointBasis = \
        self.field.basisFromString(
          self.dependenciesEntity.xmlElement.getAttribute('basis'),
          xmlElement = self.dependenciesEntity.xmlElement
        )
    else:
      self.breakpointBasis = self.field.defaultCoordinateBasis
    
    # Use the output format used for output if one isn't specified
    if not self.hasattr('outputFormat'):
      self.outputFormat = type(self.getVar('features')['Output'].outputFormat)(
        parent = self,
        **self.argumentsToTemplateConstructors
      )
    self._children.append(self.outputFormat)
    
    if self.outputFormat.name == 'hdf5':
      # HDF5 doesn't like writing out data when the order of dimensions in the file and
      # in memory aren't the same. It's slow. So we make sure that we sample in the same
      # order that we would write out to file. But only for HDF5 as this requires extra
      # MPI Transpose operations at each sample.
      driver = self._driver
      self.breakpointBasis = driver.canonicalBasisForBasis(self.breakpointBasis, noTranspose = True)
    
    self.registerVectorsRequiredInBasis(self.dependencies, self.breakpointBasis)
    
  

