#!/usr/bin/env python
# encoding: utf-8
"""
_BreakpointSegment.py

Created by Graham Dennis on 2008-03-15.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Segments._Segment import _Segment
from xpdeint.ParserException import ParserException

from xpdeint.Utilities import lazy_property

class _BreakpointSegment (_Segment):
  def __init__(self, *args, **KWs):
    _Segment.__init__(self, *args, **KWs)
    
    self.filename = None
    self.field = None
  
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
    
    if self.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
      spaceString = self.dependenciesEntity.xmlElement.getAttribute('fourier_space')
      self.breakpointBasis = \
        self.field.basisFromString(
          self.dependenciesEntity.xmlElement.getAttribute('fourier_space'),
          xmlElement = self.dependenciesEntity.xmlElement
        )
    else:
      self.breakpointBasis = self.field.defaultCoordinateBasis
    
    # Use the output format used for output if one isn't specified
    if not self.hasattr('outputFormat'):
      self.outputFormat = self.getVar('features')['Output'].outputFormat
    else:
      self._children.append(self.outputFormat)
    
    if self.outputFormat.name == 'hdf5':
      # HDF5 doesn't like writing out data when the order of dimensions in the file and
      # in memory aren't the same. It's slow. So we make sure that we sample in the same
      # order that we would write out to file. But only for HDF5 as this requires extra
      # MPI Transpose operations at each sample.
      driver = self._driver
      self.breakpointBasis = driver.canonicalBasisForBasis(self.breakpointBasis, noTranspose = True)
    
    self.registerVectorsRequiredInBasis(self.dependencies, self.breakpointBasis)
    
  

