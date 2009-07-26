#!/usr/bin/env python
# encoding: utf-8
"""
_FourierTransformFFTW3MPI.py

Created by Graham Dennis on 2008-06-08.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.Transforms.FourierTransformFFTW3 import FourierTransformFFTW3

from xpdeint.ParserException import ParserException
from xpdeint.Utilities import permutations

import operator, math
from itertools import groupby

class _FourierTransformFFTW3MPI (FourierTransformFFTW3):
  def preflight(self):
    super(_FourierTransformFFTW3MPI, self).preflight()
    
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
      for vector in [v for v in self.vectorsNeedingThisTransform if v.field == field]:
        raise ParserException(vector.xmlElement, "Vector '%s' cannot be fourier transformed because it would be distributed with MPI "
                                                 "and it doesn't have the same number of points as the geometry for the distributed dimensions." % vector)
    
    for field in [field for field in fields if not field.isDistributed]:
      for dim in [dim for dim in field.dimensions if dim.transform == self]:
        for rep in [rep for rep in dim.representations if rep and rep.hasLocalOffset]:
          dim.invalidateRepresentation(rep)
  
  def vectorNeedsPartialTransforms(self, vector):
    if not self._driver.isFieldDistributed(vector.field):
      return False
    if not vector.needsTransforms:
      return False
    # If any of the spaces in which this vector is needed are not full spaces, then we need partial transforms
    tm = self.transformMask
    if any([(space & tm) != 0 and (space & tm) != (vector.field.spaceMask & tm) for space in vector.spacesNeeded]):
      return True
    return False
  
  def initialiseForMPIWithDimensions(self, dimensions):
    # We can only upgrade to MPI support if both the first and second dimensions
    # are 'dft' or 'r2r' transforms. In the future, this restriction can be lifted
    if len(dimensions) < 2:
      raise ParserException(self._driver.xmlElement,
                            "There must be at least two dimensions to use the 'distributed-mpi' with the '%s' transform." % self.transformName[dimensions[0].name])
    if not (dimensions[0].transform == self and dimensions[1].transform == self) \
       or ((self.transformNameMap[dimensions[0].name] == 'dft') ^ (self.transformNameMap[dimensions[1].name] == 'dft')) \
       or ((self.transformNameMap[dimensions[0].name] in ['dct', 'dst']) ^ (self.transformNameMap[dimensions[1].name] in ['dct', 'dst'])):
      raise ParserException(self._driver.xmlElement,
                            "To use the 'distributed-mpi' driver with the 'dft', 'dct' or 'dst' transforms, both the first and second dimensions "
                            "must use one of these transforms with the additional restriction that if the 'dft' transform is used for one dimension "
                            "it must be used for the other.")
    
    for dim in dimensions[0:2]:
      assert self.transformNameMap[dim.name] in ['dft', 'dct', 'dst']
      # Check that the dimension doesn't have any mapping rules yet
      assert not dim._mappingRules
    
    self._driver.distributedDimensionNames = [dim.name for dim in dimensions[0:2]]
    self.mpiDimensions = dimensions[0:2]
    self.swappedSpace = reduce(operator.__or__, [dim.transformMask for dim in self.mpiDimensions])
    
    firstMPIDimension = dimensions[0]
    secondMPIDimension = dimensions[1]
    # Add additional transformed representations for the swapped case.
    for rep in firstMPIDimension.representations[:]:
      distributedRep = rep.copy(parent = firstMPIDimension)
      distributedRep.setHasLocalOffset('unswapped')
      firstMPIDimension.addRepresentation(distributedRep)
    
    for rep in secondMPIDimension.representations[:]:
      distributedRep = rep.copy(parent = secondMPIDimension)
      distributedRep.setHasLocalOffset('swapped')
      secondMPIDimension.addRepresentation(distributedRep)
    
    self.distributedMPIKinds = set([self.transformNameMap[firstMPIDimension.name]])
    if self.distributedMPIKinds.intersection(['dct', 'dst']):
      self.distributedMPIKinds.update(['dct', 'dst'])
    
  
  def mappingRulesForDimensionInField(self, dim, field):
    """
    Return default mapping rules. Each rule is a ``(mask, index)`` pair.
    A mapping rule matches a space if ``mask & space`` is nonzero. The rules
    are tried in order until one matches, and the representation correponding
    to the index in the rule is the result.
    """
    if self.isFieldDistributed(field) and dim.name in self._driver.distributedDimensionNames:
      if dim.name == self._driver.distributedDimensionNames[1]:
        return [(self.swappedSpace, 3), (dim.transformMask, 1), (None, 0)]
      else:
        return [(self.swappedSpace, 1), (dim.transformMask, 3), (None, 2)]
    return super(_FourierTransformFFTW3MPI, self).mappingRulesForDimensionInField(dim, field)
  
  
  def isFieldDistributed(self, field):
    if not field:
      return False
    return field.hasDimension(self.mpiDimensions[0]) and field.hasDimension(self.mpiDimensions[1])
  
  def sizeOfFieldInSpace(self, field, space):
    return '*'.join([dim.inSpace(space).localLattice for dim in field.dimensions])
  
  def mpiDimRepForSpace(self, space):
    return [dim.inSpace(space) for dim in self.mpiDimensions if dim.inSpace(space).hasLocalOffset][0]
  
  def fullTransformDimensionsForField(self, field):
    keyFunc = lambda x: {'dft': 'complex', 'dct': 'real', 'dst': 'real'}.get(self.transformNameMap.get(x.name))
    for transformType, dims in groupby(field.transverseDimensions, keyFunc):
      return list(dims)
  
  def isSpaceSwapped(self, space):
    return (space & self.swappedSpace) == self.swappedSpace
  
  def orderedDimensionsForFieldInSpace(self, field, space):
    """Return a list of the dimensions for field in the order in which they should be looped over"""
    dimensions = field.dimensions[:]
    if self.isSpaceSwapped(space) and self.isFieldDistributed(field):
      firstMPIDimIndex = field.indexOfDimension(self.mpiDimensions[0])
      secondMPIDimIndex = field.indexOfDimension(self.mpiDimensions[1])
      (dimensions[secondMPIDimIndex], dimensions[firstMPIDimIndex]) = (dimensions[firstMPIDimIndex], dimensions[secondMPIDimIndex])
    return dimensions
  
  def availableTransformations(self):
    results = super(_FourierTransformFFTW3MPI, self).availableTransformations()
    
    # Create transpose operations
    transposeOperations = []
    communicationsCost = None
    for firstDimRep, secondDimRep in permutations(*[dim.representations for dim in self.mpiDimensions]):
      if not communicationsCost: communicationsCost = firstDimRep.lattice * secondDimRep.lattice
      basisA = ('distributed ' + firstDimRep.name, secondDimRep.name)
      basisB = ('distributed ' + secondDimRep.name, firstDimRep.name)
      transposeOperations.append(tuple([basisA, basisB]))
    # transpose operations
    results.append(dict(
      transformations = transposeOperations,
      communicationsCost = communicationsCost,
      geometryDependent = True,
      transformType = 'real',
      transformFunction = self.transposeTransformFunction
    ))
    
    # Create mpi forward / back operations
    geometry = self.getVar('geometry')
    sortedDimNames = [(geometry.indexOfDimensionName(dimName), dimName) for dimName in self.transformNameMap]
    sortedDimNames.sort()
    sortedDimNames = [o[1] for o in sortedDimNames]
    
    untransformedDimReps = dict([(dimName, geometry.dimensionWithName(dimName).representations[0]) for dimName in sortedDimNames])
    transformedDimReps = dict([(dimName, geometry.dimensionWithName(dimName).representations[1]) for dimName in sortedDimNames])
    
    mpiTransformDimNamesLists = [self._driver.distributedDimensionNames]
    fullTransformDims = self.fullTransformDimensionsForField(geometry)
    if len(fullTransformDims) > 2:
      mpiTransformDimNamesLists.append([dim.name for dim in fullTransformDims])
    
    for dimNames in mpiTransformDimNamesLists:
      untransformedBasis = tuple(untransformedDimReps[dimName].name for dimName in dimNames)
      transformedBasis = tuple(transformedDimReps[dimName].name for dimName in dimNames)
      transformCost = self.fftCost([dimName for dimName in dimNames])
      
      results.append(dict(
        transformations = [tuple([self.canonicalBasisForBasis(untransformedBasis), self.canonicalBasisForBasis(transformedBasis)])],
        communicationsCost = communicationsCost,
        cost = transformCost,
        forwardScale = self.scaleFactorForDimReps(untransformedBasis),
        backwardScale = self.scaleFactorForDimReps(transformedBasis),
        requiresScaling = True,
        transformType = 'complex' if self.transformNameMap[self.mpiDimensions[0].name] == 'dft' else 'real',
        geometryDependent = True,
        transformFunction = self.distributedTransformFunction
      ))
    
    # Fuller forward/reverse transforms would be good in the future for the case of more than two dimensions
    # This isn't necessary for the moment though.
    
    return results
  
  def canonicalBasisForBasis(self, basis):
    if all([set(rep.canonicalName for rep in mpiDim.representations).intersection(basis) for mpiDim in self.mpiDimensions]):
      # Decide what the order is.
      basis = list(basis)
      mpiDimRepNames = [list(set(rep.canonicalName for rep in mpiDim.representations).intersection(basis))[0] for mpiDim in self.mpiDimensions]
      mpiDimRepIndices = [basis.index(rep.canonicalName) for mpiDim in self.mpiDimensions for rep in mpiDim.representations
                            if rep.canonicalName in basis]
      mpiDimRepIndices.sort()
      assert len(mpiDimRepIndices) == 2
      assert mpiDimRepIndices[1]-mpiDimRepIndices[0] == 1
      basisSlice = slice(mpiDimRepIndices[0], mpiDimRepIndices[1]+1)
      if all(any([rep.canonicalName in mpiDimRepNames for rep in mpiDim.representations if rep.tag == self.fourierSpaceTag]) for mpiDim in self.mpiDimensions):
        # Then we are swapped
        basis[basisSlice] = reversed([b.replace('distributed ','') for b in mpiDimRepNames])
      else:
        basis[basisSlice] = [b.replace('distributed ','') for b in mpiDimRepNames]
      
      basis[basisSlice.start] = 'distributed ' + basis[basisSlice.start]
      basis = tuple(basis)
    else:
      # At most one of the mpi dimensions is in this basis. Therefore we must ensure that no part of the basis contains 'distributed '
      basis = tuple(b.replace('distributed ','') for b in basis)
    
    assert sum('distributed ' in b for b in basis) <= 1
    return basis
  

