#!/usr/bin/env python
# encoding: utf-8
"""
_FourierTransformFFTW3MPI.py

Created by Graham Dennis on 2008-06-08.

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

from xpdeint.Features.Transforms.FourierTransformFFTW3 import FourierTransformFFTW3

from xpdeint.ParserException import ParserException
from xpdeint.Utilities import permutations, lazy_property

import operator
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
  
  def initialiseForMPIWithDimensions(self, dimensions):
    # We can only upgrade to MPI support if both the first and second dimensions
    # are 'dft' or 'r2r' transforms. In the future, this restriction can be lifted
    if len(dimensions) < 2:
      raise ParserException(self._driver.xmlElement,
                            "There must be at least two dimensions to use the 'distributed-mpi' with the '%s' transform." % self.transformName[dimensions[0].name])
    if len(dimensions[0].representations) <= 1 or len(dimensions[1].representations) <= 1:
      raise ParserException(
        self._driver.xmlElement,
        "To use the 'distributed-mpi' driver either the first dimension must have no transform or "
        "the first two dimensions must both have transforms."
      )
    
    self._driver.distributedDimensionNames = [dim.name for dim in dimensions[0:2]]
    self.mpiDimensions = dimensions[0:2]
    
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
    
  
  def isFieldDistributed(self, field):
    if not field:
      return False
    return field.hasDimension(self.mpiDimensions[0]) and field.hasDimension(self.mpiDimensions[1])
  
  @lazy_property
  def hasFFTWDistributedTransforms(self):
    geometry = self.getVar('geometry')
    return True if self.fullTransformDimensionsForField(geometry) else False
  
  def fullTransformDimensionsForField(self, field):
    keyFunc = lambda x: {'dft': 'complex', 'dct': 'real', 'dst': 'real'}.get(self.transformNameMap.get(x.name))
    for transformType, dims in groupby(field.transverseDimensions, keyFunc):
      return list(dims) if transformType else []
  
  @property
  def vectorsNeedingDistributedTransforms(self):
    result = set()
    [result.update(transformationDict['vectors']) 
      for tID, transformationDict in self.transformations if transformationDict.get('distributedTransform', False)]
    return result
  
  def availableTransformations(self):
    parent_results = super(_FourierTransformFFTW3MPI, self).availableTransformations()
    
    results = []
    
    # Create mpi forward / back operations
    geometry = self.getVar('geometry')
    sortedDimNames = [(geometry.indexOfDimensionName(dimName), dimName) for dimName in self.transformNameMap]
    sortedDimNames.sort()
    sortedDimNames = [o[1] for o in sortedDimNames]
    
    untransformedDimReps = dict([(dimName, geometry.dimensionWithName(dimName).firstDimRepWithTagName('coordinate')) for dimName in sortedDimNames])
    transformedDimReps = dict([(dimName, geometry.dimensionWithName(dimName).firstDimRepWithTagName('spectral')) for dimName in sortedDimNames])
    
    mpiTransformDimNamesLists = []
    fullTransformDims = self.fullTransformDimensionsForField(geometry)
    if len(fullTransformDims) > 2:
      mpiTransformDimNamesLists.append([dim.name for dim in fullTransformDims])
    if len(fullTransformDims) >= 2:
      mpiTransformDimNamesLists.append([dim.name for dim in fullTransformDims[0:2]])
    
    for dimNames in mpiTransformDimNamesLists:
      untransformedBasis = tuple(untransformedDimReps[dimName].name for dimName in dimNames)
      transformedBasis = tuple(transformedDimReps[dimName].name for dimName in dimNames)
      transformCost = self.fftCost([dimName for dimName in dimNames])
      communicationsCost = reduce(operator.mul, [untransformedDimReps[dimName].latticeEstimate for dimName in dimNames])
      
      results.append(dict(
        transformations = [tuple([self.canonicalBasisForBasis(untransformedBasis), self.canonicalBasisForBasis(transformedBasis)])],
        communicationsCost = communicationsCost,
        cost = transformCost,
        distributedTransform = True,
        forwardScale = self.scaleFactorForDimReps(untransformedBasis),
        backwardScale = self.scaleFactorForDimReps(transformedBasis),
        requiresScaling = True,
        transformType = 'complex' if self.transformNameMap[self.mpiDimensions[0].name] == 'dft' else 'real',
        geometryDependent = True,
        transformFunction = self.distributedTransformFunction
      ))
    
    # Create transpose operations
    transposeOperations = []
    for firstDimRep, secondDimRep in permutations(*[[rep for rep in dim.representations if not rep.hasLocalOffset] for dim in self.mpiDimensions]):
      communicationsCost = firstDimRep.latticeEstimate * secondDimRep.latticeEstimate
      basisA = ('distributed ' + firstDimRep.name, secondDimRep.name)
      basisB = ('distributed ' + secondDimRep.name, firstDimRep.name)
      if not self.hasFFTWDistributedTransforms:
        basisA = tuple(reversed(basisA))
        basisB = tuple(reversed(basisB))
      results.append(dict(
        transformations = [tuple([basisA, basisB])],
        communicationsCost = communicationsCost,
        geometryDependent = True,
        transformType = 'real',
        distributedTransform = True,
        transformFunction = self.transposeTransformFunction,
        transposedOrder = not self.hasFFTWDistributedTransforms,
      ))
    
    final_transforms = []
    for transform in results:
      final_transforms.append(transform.copy())
      transform['outOfPlace'] = True
      final_transforms.append(transform)
    
    return parent_results + final_transforms
  
  def canonicalBasisForBasis(self, basis, noTranspose = False):
    if all([set(rep.canonicalName for rep in mpiDim.representations).intersection(basis) for mpiDim in self.mpiDimensions]):
      # Decide what the order is.
      basis = list(basis)
      mpiDimRepNames = [rep.canonicalName for mpiDim in self.mpiDimensions for rep in mpiDim.representations if rep.canonicalName in basis]
      mpiDimRepIndices = [basis.index(rep.canonicalName) for mpiDim in self.mpiDimensions for rep in mpiDim.representations
                            if rep.canonicalName in basis]
      mpiDimRepIndices.sort()
      assert len(mpiDimRepIndices) == 2
      assert mpiDimRepIndices[1] - mpiDimRepIndices[0] == 1
      basisSlice = slice(mpiDimRepIndices[0], mpiDimRepIndices[1]+1)
      
      nonDistributedMPIDimRepNames = [b.replace('distributed ', '') for b in mpiDimRepNames]
      
      if (not noTranspose) and sum(b.startswith('distributed ') for b in basis[basisSlice]) == 1:
        # Transposes are legal, and the basis is already propery distributed.
        # Leave it alone.
        pass
      else:
        if (not noTranspose) \
            and all([any([rep.canonicalName in mpiDimRepNames
                            for rep in mpiDim.representations if issubclass(rep.tag, rep.tagForName('spectral'))])
                      for mpiDim in self.mpiDimensions]):
          # Transposes are legal and all MPI dimensions are in spectral representations.
          # We decide that this means we are swapped.
          basis[basisSlice] = reversed(nonDistributedMPIDimRepNames)
        else:
          # Either transposes aren't legal or not all MPI dimensions were in spectral representation.
          basis[basisSlice] = nonDistributedMPIDimRepNames
        
        distributedIdx = basisSlice.start if self.hasFFTWDistributedTransforms else basisSlice.start + 1
        basis[distributedIdx] = 'distributed ' + basis[distributedIdx]
      basis = tuple(basis)
    else:
      # At most one of the mpi dimensions is in this basis. Therefore we must ensure that no part of the basis contains 'distributed '
      basis = tuple(b.replace('distributed ','') for b in basis)
    
    assert sum('distributed ' in b for b in basis) <= 1
    return basis
  

