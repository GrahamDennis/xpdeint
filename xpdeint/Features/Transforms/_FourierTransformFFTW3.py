#!/usr/bin/env python
# encoding: utf-8
"""
_FourierTransform.py

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

from xpdeint.Features.Transforms._Transform import _Transform

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.SplitUniformDimensionRepresentation import SplitUniformDimensionRepresentation

from xpdeint.Utilities import lazy_property

import math, operator, types
from itertools import groupby

class _FourierTransformFFTW3 (_Transform):
  transformName = 'FourierTransform'
  fftwSuffix = ''
  
  coordinateSpaceTag = DimensionRepresentation.registerTag('FFTW coordinate space', parent = 'coordinate')
  fourierSpaceTag = DimensionRepresentation.registerTag('FFTW Fourier space', parent = 'spectral')
  
  def __init__(self, *args, **KWs):
    _Transform.__init__(self, *args, **KWs)
    self.transformNameMap = {}
  
  @lazy_property
  def fftwPrefix(self):
    precision = self.getVar('precision')
    return {'double': 'fftw', 'single': 'fftwf'}[precision]
  
  @lazy_property
  def fftwLibVersionName(self):
      return {'fftw': 'fftw3', 'fftwf': 'fftw3f'}[self.fftwPrefix]
  
  @lazy_property
  def wisdomExtension(self):
    result = '.' + self.fftwLibVersionName
    if self.fftwSuffix:
      result += '_' + self.fftwSuffix
    return result
  
  @lazy_property
  def uselib(self):
    result = [self.fftwLibVersionName]
    if self.fftwSuffix:
      result.append(self.fftwLibVersionName + '_' + self.fftwSuffix)
    return result
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   spectralLattice = None,
                   type = 'real', volumePrefactor = None,
                   xmlElement = None):
    assert type == 'real'
    assert transformName in ['dft', 'dct', 'dst']
    dim = super(_FourierTransformFFTW3, self).newDimension(name, lattice, minimum, maximum,
                                                           parent, transformName, aliases,
                                                           type, volumePrefactor, xmlElement)
    self.transformNameMap[dim.name] = transformName
    if transformName == 'dft':
      # x-space representation
      xspace = UniformDimensionRepresentation(name = name, type = type, runtimeLattice = lattice,
                                              _minimum = minimum, _maximum = maximum, parent = dim,
                                              tag = self.coordinateSpaceTag,
                                              **self.argumentsToTemplateConstructors)
      # kspace representation
      kspace = SplitUniformDimensionRepresentation(
        name = 'k' + name, type = type, runtimeLattice = lattice,
        _range = '%s - %s' % (xspace.maximum, xspace.minimum),
        parent = dim, tag = self.fourierSpaceTag,
        reductionMethod = SplitUniformDimensionRepresentation.ReductionMethod.fixedStep,
        **self.argumentsToTemplateConstructors
      )
    else:
      # x-space representation
      stepSize = '((real)%(maximum)s - %(minimum)s)/(%(lattice)s)' % locals()
      xspace = UniformDimensionRepresentation(
        name = name, type = type, runtimeLattice = lattice,
        _stepSize = stepSize, tag = self.coordinateSpaceTag,
        parent = dim, **self.argumentsToTemplateConstructors
      )
      # Modify the minimum and maximum values to deal with the 0.5*stepSize offset
      xspace._minimum = '%s + 0.5*%s' % (minimum, xspace.stepSize)
      xspace._maximum = '%s + 0.5*%s' % (maximum, xspace.stepSize)
      if transformName == 'dct':
        # kspace representation
        kspace = UniformDimensionRepresentation(
          name = 'k' + name, type = type, runtimeLattice = lattice,
          _minimum = '0.0', _stepSize = '(M_PI/(%(maximum)s - %(minimum)s))' % locals(),
          tag = self.fourierSpaceTag,
          reductionMethod = UniformDimensionRepresentation.ReductionMethod.fixedStep,
          parent = dim, **self.argumentsToTemplateConstructors
        )
        kspace._maximum = '%s * %s' % (kspace.stepSize, kspace.globalLattice)
      else:
        kspace = UniformDimensionRepresentation(
          name = 'k' + name, type = type, runtimeLattice = lattice,
          _stepSize = '(M_PI/(%(maximum)s - %(minimum)s))' % locals(),
          tag = self.fourierSpaceTag,
          reductionMethod = UniformDimensionRepresentation.ReductionMethod.fixedStep,
          parent = dim, **self.argumentsToTemplateConstructors
        )
        kspace._minimum = '%s' % kspace.stepSize
        kspace._maximum = '%s * (%s + 1)' % (kspace.stepSize, kspace.globalLattice)
    
    dim.addRepresentation(xspace)
    dim.addRepresentation(kspace)
    return dim
  
  def r2rKindForDimensionAndDirection(self, dim, direction):
    dimName = dim.name if not isinstance(dim, types.StringTypes) else dim
    transformName = self.transformNameMap[dimName]
    return {'dct': {'forward': 'FFTW_REDFT10', 'backward': 'FFTW_REDFT01'},
            'dst': {'forward': 'FFTW_RODFT10', 'backward': 'FFTW_RODFT01'}}[transformName][direction]
  
  def fftCost(self, dimNames):
    geometry = self.getVar('geometry')
    untransformedDimReps = dict([(dimName, geometry.dimensionWithName(dimName).representations[0]) for dimName in dimNames])
    cost = sum([int(math.ceil(math.log(untransformedDimReps[dimName].latticeEstimate))) for dimName in dimNames], 0)
    cost *= reduce(operator.mul, [untransformedDimReps[dimName].latticeEstimate for dimName in dimNames], 1)
    return cost
  
  @staticmethod
  def scaleFactorForDimReps(dimReps):
    return ' * '.join(['_inverse_sqrt_2pi * _d' + dimRepName for dimRepName in dimReps])
  
  def availableTransformations(self):
    results = []
    geometry = self.getVar('geometry')
    sortedDimNames = [(geometry.indexOfDimensionName(dimName), dimName) for dimName in self.transformNameMap]
    sortedDimNames.sort()
    sortedDimNames = [o[1] for o in sortedDimNames]
    
    transformFunctions = dict(
      geometryDependent = True,
      transformFunction = self.transformFunction,
    )
    
    for dimName in sortedDimNames:
      dimReps = [rep for rep in geometry.dimensionWithName(dimName).representations if not rep.hasLocalOffset]
      results.append(dict(
        transformations = [tuple(rep.name for rep in dimReps)],
        cost = self.fftCost([dimName]),
        forwardScale = self.scaleFactorForDimReps([dimReps[0].name]),
        backwardScale = self.scaleFactorForDimReps([dimReps[1].name]),
        requiresScaling = True,
        transformType = 'complex' if self.transformNameMap[dimName] == 'dft' else 'real',
        **transformFunctions
      ))
    
    if self.hasattr('mpiDimensions'):
      for dim in [dim for dim in self.mpiDimensions if dim.name in sortedDimNames]:
        sortedDimNames.remove(dim.name)
    
    c2cDimNames = [dimName for dimName in sortedDimNames if self.transformNameMap[dimName] == 'dft']
    r2rDimNames = [dimName for dimName in sortedDimNames if self.transformNameMap[dimName] in ['dct', 'dst']]
    
    untransformedDimReps = dict([(dimName, geometry.dimensionWithName(dimName).representations[0]) for dimName in sortedDimNames])
    transformedDimReps = dict([(dimName, geometry.dimensionWithName(dimName).representations[1]) for dimName in sortedDimNames])
    
    # Create optimised forward/backward transforms
    keyFunc = lambda x: {'dft': 'complex', 'dct': 'real', 'dst': 'real'}[self.transformNameMap[x]]
    for transformType, dimNames in groupby(sortedDimNames, keyFunc):
      dimNames = list(dimNames)
      if len(dimNames) <= 1: continue
      cost = self.fftCost(dimNames)
      untransformedBasis = tuple(untransformedDimReps[dimName].name for dimName in dimNames)
      transformedBasis = tuple(transformedDimReps[dimName].name for dimName in dimNames)
      bases = tuple([untransformedBasis, transformedBasis])
      results.append(dict(
        transformations = [bases],
        cost = cost,
        forwardScale = self.scaleFactorForDimReps(untransformedBasis),
        backwardScale = self.scaleFactorForDimReps(transformedBasis),
        requiresScaling = True,
        transformType = transformType,
        **transformFunctions
      ))
    
    final_transforms = []
    for transform in results:
      final_transforms.append(transform.copy())
      transform['outOfPlace'] = True
      final_transforms.append(transform)
    
    return final_transforms
  

