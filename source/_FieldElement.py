#!/usr/bin/env python
# encoding: utf-8
"""
_FieldElement.py

This contains all the pure-python code for FieldElement.tmpl

Created by Graham Dennis on 2007-10-17.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from ScriptElement import ScriptElement

class _FieldElement (ScriptElement):
  def __init__(self, *args, **KWs):
    # The MomentGroup and GeometryElement subclasses define name properties
    if not hasattr(self, 'name'):
      self.name = KWs['name']
      del KWs['name']
    
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.isOutputField = False
    self.managedVectors = set()
    self.temporaryVectors = set()
    self.dimensions = []
    
    self.getVar('fields').append(self)
    self.getVar('scriptElements').append(self)
  
  @property
  def vectors(self):
    returnValue = self.managedVectors.copy()
    returnValue.update(self.temporaryVectors)
    return returnValue
  
  @property
  def children(self):
    return self.managedVectors.copy()
  
  # The space mask for this field
  # i.e. which parts of the space variable we care about
  @property
  def spaceMask(self):
    bitMask = 0
    
    geometryElement = self.getVar('geometry')
    
    for dimensionNumber, dimension in enumerate(geometryElement.dimensions):
      if self.hasDimension(dimension):
        bitMask |= 1 << dimensionNumber
    
    return bitMask
  
  # Do we have the dimension?
  def hasDimension(self, dimension):
    return self.hasDimensionName(dimension.name)
  
  # Do we have a dimension matching dimensionName?
  def hasDimensionName(self, dimensionName):
    dimensionList = filter(lambda x: x.name == dimensionName, self.dimensions)
    assert len(dimensionList) <= 1
    
    if len(dimensionList):
      return True
    else:
      return False
  
  # Is the field a subset of another field (in terms of dimensions)
  def isSubsetOfField(self, field):
    for dimension in self.dimensions:
      if not field.hasDimension(dimension):
        return False
    return True
  
  
  # The index of the provided dimension
  def indexOfDimension(self, dimension):
    return self.indexOfDimensionName(dimension.name)

  # The index of the dimension with the name dimensionName
  def indexOfDimensionName(self, dimensionName):
    dimensionList = filter(lambda x: x.name == dimensionName, self.dimensions)
    assert len(dimensionList) == 1
    return self.dimensions.index(dimensionList[0])
  
  # Return a string which is the number of points in the dimensions corresponding to the passed indices
  def pointsInDimensionsWithIndices(self, indices):
    if len(indices) == 0:
      return '1'
    
    result = []
    separator = ''
    for dimensionIndex in indices:
      # Only put a multiply sign in for everything after the first dimension
      result.append(separator)
      separator = ' * '
      result.extend(['_', self.name, '_lattice', str(dimensionIndex)])
    
    return ''.join(result)
  
  @property
  def pointsInDimensionsNumerically(self):
    points = 1
    for dimension in self.dimensions:
      points *= int(dimension.lattice)
    
    return points
  
  @property
  def integerValuedDimensions(self):
    result = []
    
    dimensionList = []
    
    for dim in self.dimensions:
      # Once we hit a double dimension, we must have passed
      # the 'first' integer valued dimensions if we have any
      if dim.type == 'double':
        if dimensionList:
          result.append(dimensionList)
          dimensionList = []
      elif dim.type == 'long':
        dimensionList.append(dim)
      else:
        # Badness
        assert False
    
    if dimensionList:
      result.append(dimensionList)
    return result
  
  # Dimension overrides
  def dimensionOverrides(self):
    return filter(lambda x: hasattr(x, 'override'), self.dimensions)
  
  # Initialise field
  def initialise(self):
    return self.implementationsForChildren('initialise')
  
  # Allocate (and initialise active pointers)
  def allocate(self):
    return self.implementationsForChildren('allocate')
  
  # Free vectors
  def free(self):
    return self.implementationsForChildren('free')
  
  def volumeElementInSpace(self, space):
    assert len(filter(lambda x: x.fourier, self.dimensions)) > 0
    result = []
    separator = ''
    result.append('(')
    for dimension in filter(lambda x: x.fourier, self.dimensions):
      if self.dimensionIsInFourierSpace(dimension, space):
        dimensionPrefix = 'k'
      else:
        dimensionPrefix = 'x'
      
      result.extend([separator, '_', self.name, '_d', dimensionPrefix, str(self.indexOfDimension(dimension))])
      separator = ' * '
    result.append(')')
    
    return ''.join(result)
  
  def sortDimensions(self):
    """Sort the dimensions of the field into canonical (geometry element) order."""
    geometryTemplate = self.getVar('geometry')
    sortFunction = lambda x, y: cmp(geometryTemplate.indexOfDimension(x), geometryTemplate.indexOfDimension(y))
    self.dimensions.sort(sortFunction)
  

