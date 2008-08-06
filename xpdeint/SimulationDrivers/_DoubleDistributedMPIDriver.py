#!/usr/bin/env python
# encoding: utf-8
"""
_DoubleDistributedMPIDriver.py

Created by Graham Dennis on 2008-04-05.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.SimulationDrivers.DistributedMPIDriver import DistributedMPIDriver
from xpdeint.Features.FourierTransformFFTW3 import FourierTransformFFTW3
from xpdeint.Features.FourierTransformFFTW3MPI import FourierTransformFFTW3MPI

# import xpdeint.Geometry.DoubleDimension

from xpdeint.ParserException import ParserException

class _DoubleDistributedMPIDriver (DistributedMPIDriver):
  def __init__(self, *args, **KWs):
    DistributedMPIDriver.__init__(self, *args, **KWs)
    
    transverseDimensions = self.getVar('geometry').transverseDimensions
    assert len(transverseDimensions) >= 2
    self.firstMPIDimension = transverseDimensions[0]
    assert isinstance(self.firstMPIDimension, xpdeint.Geometry.DoubleDimension.DoubleDimension)
    self.distributedDimensionNames.append(self.firstMPIDimension.name)
    self.secondMPIDimension = transverseDimensions[1]
    assert isinstance(self.secondMPIDimension, xpdeint.Geometry.DoubleDimension.DoubleDimension)
    self.distributedDimensionNames.append(self.secondMPIDimension.name)
    
    features = self.getVar('features')
    fftImplementation = features['FourierTransform']
    if not type(fftImplementation) == FourierTransformFFTW3:
      raise ParserException(self.xmlElement, "When using the 'distributed-mpi' driver, the fourier transform implementation must be fftw3.\n"
                                             "There cannot be a thread attribute. The implementation currently being used is: %s\n" % type(fftImplementation))
    # This is incredibly, incredibly dodgy. But I'm doing it this way as I can't think of a better way.
    # If someone who knows Python better than I knows what could go wrong with this line of code, please
    # send an email to xmds-devel@lists.sourceforge.net
    # Note that FourierTransformFFTW3MPI does not define any attributes that do not already exist in FourierTransformFFTW3
    # <dodgy>
    fftImplementation.__class__ = FourierTransformFFTW3MPI
    # </dodgy>
  
  @property
  def geometryVariableSuffixesToBeShadowed(self):
    """
    Return the geometry variable suffixes that need to be shadowed when doing a binary
    write-out of data that exists on multiple nodes. By shadowing these variables, rank
    0 can pretend to be another rank for the purpose of looping.
    """
    suffixes = ['_local_unswapped_lattice_',  '_local_unswapped_offset_',
                '_local_unswapped_lattice_k', '_local_unswapped_offset_k',
                '_local_swapped_lattice_k',   '_local_swapped_offset_k']
    
    result = []
    for dimName in [self.firstMPIDimension.name, self.secondMPIDimension.name]:
      result.extend([s + dimName for s in suffixes])
    
    return result
  
  def isSpaceSwapped(self, space):
    return self.dimensionIsInFourierSpace(self.firstMPIDimension, space) and self.dimensionIsInFourierSpace(self.secondMPIDimension, space)
  
  def mpiDimensionForSpace(self, space):
    return self.isSpaceSwapped(space) and self.secondMPIDimension or self.firstMPIDimension
  
  def isFieldDistributed(self, field):
    return field.hasDimension(self.firstMPIDimension) and field.hasDimension(self.secondMPIDimension)
  
  def mayHaveLocalOffsetForDimensionInFieldInSpace(self, dimension, field, space):
    if not self.isFieldDistributed(field):
      return False
    
    if self.isSpaceSwapped(space):
      return dimension.name == self.secondMPIDimension.name
    else:
      return dimension.name == self.firstMPIDimension.name
  
  def localOffsetForDimensionInFieldInSpace(self, dimension, field, space):
    if not (self.isFieldDistributed(field) and self.mayHaveLocalOffsetForDimensionInFieldInSpace(dimension, field, space)):
      return "0"
    
    if self.isSpaceSwapped(space):
      spaceType = 'swapped'
    else:
      spaceType = 'unswapped'
    return ''.join(['_', field.name, '_local_', spaceType, '_offset_', self.dimensionNameForSpace(dimension, space)])
  
  def localLatticeForDimensionInFieldInSpace(self, dimension, field, space):
    if not (self.isFieldDistributed(field) and self.mayHaveLocalOffsetForDimensionInFieldInSpace(dimension, field, space)):
      return ''.join(['_', field.name, '_lattice_', self.dimensionNameForSpace(dimension, space)])
    if self.isSpaceSwapped(space):
      spaceType = 'swapped'
    else:
      spaceType = 'unswapped'
    return ''.join(['_', field.name, '_local_', spaceType, '_lattice_', self.dimensionNameForSpace(dimension, space)])
  
  def orderedDimensionsForFieldInSpace(self, field, space):
    """Return a list of the dimensions for field in the order in which they should be looped over"""
    dimensions = super(_DoubleDistributedMPIDriver, self).orderedDimensionsForFieldInSpace(field, space)
    if self.isSpaceSwapped(space) and self.isFieldDistributed(field):
      firstMPIDimIndex = dimensions.index(self.firstMPIDimension)
      secondMPIDimIndex = dimensions.index(self.secondMPIDimension)
      (dimensions[secondMPIDimIndex], dimensions[firstMPIDimIndex]) = (dimensions[firstMPIDimIndex], dimensions[secondMPIDimIndex])
    return dimensions
  
  

