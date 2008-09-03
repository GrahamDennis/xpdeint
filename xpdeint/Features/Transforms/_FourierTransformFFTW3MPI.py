#!/usr/bin/env python
# encoding: utf-8
"""
_FourierTransformFFTW3MPI.py

Created by Graham Dennis on 2008-06-08.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms.FourierTransformFFTW3 import FourierTransformFFTW3

from xpdeint.ParserException import ParserException

import operator

class _FourierTransformFFTW3MPI (FourierTransformFFTW3):
  def preflight(self):
    fields = self.getVar('fields')
    geometry = self.getVar('geometry')
    driver = self._driver
    
    # Check that all vectors that are distributed and need fourier transforms
    # contain all the points in the MPI dimensions. Otherwise we can't fourier
    # transform them.
    for field in filter(driver.isFieldDistributed, fields):
      # If all the distributed dimensions are the same in this field as in the geometry, then everything is OK
      if all([field.dimensionWithName(name) == geometry.dimensionWithName(name) for name in driver.distributedDimensionNames]):
        continue
      for vector in filter(lambda x: x.needsTransforms, field.vectors):
        raise ParserException(vector.xmlElement, "Vector '%s' cannot be fourier transformed because it would be distributed with MPI\n"
                                                 "and it doesn't have the same number of points as the geometry for the distributed dimensions." % vector)
    
    for field in fields:
      if not field.isDistributed:
        for dim in [dim for dim in field.dimensions if dim.transform == self]:
          if len(dim.representations) > 2:
            dim.invalidateRepresentation(dim.representations[2])
            del dim.representations[2]
          for rep in dim.representations:
            if rep:
              rep.setHasLocalOffset(None)
  
  def vectorNeedsPartialTransforms(self, vector):
    if not self._driver.isFieldDistributed(vector.field):
      return False
    if not vector.needsTransforms:
      return False
    # If any of the spaces in which this vector is needed are not full spaces, then we need partial transforms
    if any([space != 0 and space != vector.field.spaceMask for space in vector.spacesNeeded]):
      return True
    return False
  
  def initialiseForMPIWithDimensions(self, dimensions):
    # It has already been checked by _FourierTransformFFTW3 that we can handle these dimensions
    # but let's just run a couple of assert's to make sure
    assert not ((self.transformNameMap[dimensions[0].name] == 'dft') ^ (self.transformNameMap[dimensions[1].name] == 'dft'))
    assert not ((self.transformNameMap[dimensions[0].name] in ['dct', 'dst']) ^ (self.transformNameMap[dimensions[1].name] in ['dct', 'dst']))
    for dim in dimensions[0:2]:
      assert self.transformNameMap[dim.name] in ['dft', 'dct', 'dst']
      # Check that the dimension doesn't have any mapping rules yet
      assert not dim._mappingRules
    
    for dim in dimensions[0:2]:
      self.transformNameMap[dim.name] = 'mpi-' + self.transformNameMap[dim.name]
    
    self._driver.distributedDimensionNames = [dim.name for dim in dimensions[0:2]]
    self.mpiDimensions = dimensions[0:2]
    self.swappedSpace = reduce(operator.__or__, [dim.transformMask for dim in self.mpiDimensions])
    self.getVar('transforms')['mpi-dft'] = self
    self.getVar('transforms')['mpi-dct'] = self
    self.getVar('transforms')['mpi-dst'] = self
    
    firstMPIDimension = dimensions[0]
    secondMPIDimension = dimensions[1]
    # Add additional transformed representations for the swapped case.
    firstMPIDimension.addRepresentation(firstMPIDimension.inSpace(firstMPIDimension.transformMask).copy())
    firstMPIDimension.inSpace(0).setHasLocalOffset('unswapped')
    firstMPIDimension.inSpace(firstMPIDimension.transformMask).setHasLocalOffset('unswapped')
    
    secondMPIDimension.addRepresentation(secondMPIDimension.inSpace(secondMPIDimension.transformMask).copy())
    secondMPIDimension.inSpace(self.swappedSpace).setHasLocalOffset('swapped')
    
    self.distributedMPIKinds = set([self.transformNameMap[firstMPIDimension.name]])
    if self.distributedMPIKinds.intersection(['mpi-dct', 'mpi-dst']):
      self.distributedMPIKinds.update(['dct', 'dst', 'mpi-dct', 'mpi-dst'])
    if 'mpi-dft' in self.distributedMPIKinds:
      self.distributedMPIKinds.add('dft')
    
  
  def mappingRulesForDimensionInField(self, dim, field):
    """
    Return default mapping rules. Each rule is a ``(mask, index)`` pair.
    A mapping rule matches a space if ``mask & space`` is nonzero. The rules
    are tried in order until one matches, and the representation correponding
    to the index in the rule is the result.
    """
    if self.isFieldDistributed(field) and dim.name in self._driver.distributedDimensionNames:
      return [(self.swappedSpace, 2), (dim.transformMask, 1), (None, 0)]
    return super(_FourierTransformFFTW3MPI, self).mappingRulesForDimensionInField(dim, field)
  
  
  def isFieldDistributed(self, field):
    if not field:
      return False
    return field.hasDimension(self.mpiDimensions[0]) and field.hasDimension(self.mpiDimensions[1])
  
  def mpiDimensionForSpace(self, space):
    return [dim for dim in self.mpiDimensions if dim.inSpace(space).hasLocalOffset][0]
  
  def fullTransformDimensionsForField(self, field):
    result = []
    for dim in field.transverseDimensions:
      if not self.transformNameMap.get(dim.name) in self.distributedMPIKinds:
        break
      result.append(dim)
    return result
  
  def isSpaceSwapped(self, space):
    return (space & self.swappedSpace) == self.swappedSpace
  
  def orderedDimensionsForFieldInSpace(self, field, space):
    """Return a list of the dimensions for field in the order in which they should be looped over"""
    dimensions = field.dimensions[:]
    if self.isSpaceSwapped(space) and self.isFieldDistributed(field):
      firstMPIDimIndex = dimensions.index(self.mpiDimensions[0])
      secondMPIDimIndex = dimensions.index(self.mpiDimensions[1])
      (dimensions[secondMPIDimIndex], dimensions[firstMPIDimIndex]) = (dimensions[firstMPIDimIndex], dimensions[secondMPIDimIndex])
    return dimensions
  

