#!/usr/bin/env python
# encoding: utf-8
"""
_FieldElement.py

This contains all the pure-python code for FieldElement.tmpl

Created by Graham Dennis on 2007-10-17.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

from xpdeint import RegularExpressionStrings
from xpdeint.ParserException import ParserException

from xpdeint.Utilities import lazy_property

class _FieldElement (ScriptElement):
  def __init__(self, *args, **KWs):
    # The MomentGroup and GeometryElement subclasses define name properties
    if not self.hasattr('name'):
      self.name = KWs['name']
      del KWs['name']
    if not 'parent' in KWs: KWs['parent'] = self.simulation
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.managedVectors = set()
    self.temporaryVectors = set()
    self.dimensions = []
    
    self.getVar('fields').append(self)
  
  @property
  def vectors(self):
    returnValue = self.managedVectors.copy()
    returnValue.update(self.temporaryVectors)
    return returnValue
  
  @property
  def children(self):
    children = super(_FieldElement, self).children
    children.extend(self.dimensions)
    # Sort managed vectors by name
    children.extend(self.managedVectors)
    return children
  
  # The space mask for this field
  # i.e. which parts of the space variable we care about
  @lazy_property
  def spaceMask(self):
    """
    Return the spaceMask for this field, i.e. which part of a spaces variable
    that is relevant to this field.
    """
    bitMask = 0
    
    geometryElement = self.getVar('geometry')
    
    for dimensionNumber, dimension in enumerate(geometryElement.dimensions):
      if self.hasDimension(dimension) and dimension.isTransformable:
        bitMask |= dimension.transformMask
    
    return bitMask
  
  @lazy_property
  def prefix(self):
    if not self.name == 'geometry':
      return '_' + self.name
    else:
      return ''
  
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
    """Return whether this field's dimensions are a subset of the dimensions of field `field`."""
    for dimension in self.dimensions:
      if not field.hasDimension(dimension):
        return False
    return True
  
  def isEquivalentToField(self, field):
    """Return whether this field and field `field` have the same dimensions."""
    return self.isSubsetOfField(field) and field.isSubsetOfField(self)
  
  # The index of the provided dimension
  def indexOfDimension(self, dimension):
    """Return the index (in the `dimensions` list) of the dimension corresponding to `dimension`."""
    return self.indexOfDimensionName(dimension.name)
  
  # The index of the dimension with the name dimensionName
  def indexOfDimensionName(self, dimensionName):
    """Return the index (in the `dimensions` list) of the dimension that has the name `dimensionName`."""
    dimensionList = filter(lambda x: x.name == dimensionName, self.dimensions)
    assert len(dimensionList) == 1
    return self.dimensions.index(dimensionList[0])
  
  def dimensionWithName(self, dimensionName):
    """Return the dimension that has the name `dimensionName`."""
    return self.dimensions[self.indexOfDimensionName(dimensionName)]
  
  # Return a string which is the number of points in the dimensions corresponding to the passed indices
  def pointsInDimensionsWithIndices(self, indices):
    if len(indices) == 0:
      return '1'
    
    result = []
    separator = ''
    for dimensionIndex in indices:
      assert dimensionIndex < len(self.dimensions)
      # Only put a multiply sign in for everything after the first dimension
      result.append(separator)
      separator = ' * '
      maxRep = max([(rep.lattice, rep) for rep in self.dimensions[dimensionIndex].representations if rep])[1]
      result.append(maxRep.globalLattice)
    
    return ''.join(result)
  
  # Return a string which is the number of points in the dimensions corresponding to the passed indices
  def localPointsInDimensionsWithIndicesInSpace(self, indices, space):
    if len(indices) == 0:
      return '1'
    
    result = []
    separator = ''
    for dimensionIndex in indices:
      assert dimensionIndex < len(self.dimensions)
      # Only put a multiply sign in for everything after the first dimension
      result.append(separator)
      separator = ' * '
      result.append(self.dimensions[dimensionIndex].inSpace(space).localLattice)
    
    return ''.join(result)
  
  def localPointsInDimensionsAfterDimensionInSpace(self, dimension, space):
    assert self.hasDimension(dimension)
    orderedDimensions = self.orderedDimensionsInSpace(space)
    # Grab everything after dimension
    orderedDimensions = orderedDimensions[(orderedDimensions.index(dimension)+1):]
    indices = [self.dimensions.index(dim) for dim in orderedDimensions]
    return self.localPointsInDimensionsWithIndicesInSpace(indices, space)
  
  @lazy_property
  def maxPoints(self):
    points = 1
    for dimension in self.dimensions:
      points *= max([rep.lattice for rep in dimension.representations])
    
    return points
  
  @property
  def transverseDimensions(self):
    return filter(lambda x: x.transverse, self.dimensions)
  
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
    reps = [d.inSpace(space) for d in self.dimensions]
    if all([rep.type == 'long' for rep in reps]):
      return '1.0'
    result = []
    separator = ''
    result.append('(')
    for rep in filter(lambda x: x.type == 'double', reps):
      result.extend([separator, rep.stepSize])
      separator = ' * '
    result.append(')')
    
    return ''.join(result)
  
  @lazy_property
  def isDistributed(self):
    return self._driver.isFieldDistributed(self)
  
  def orderedDimensionsInSpace(self, space):
    """Return a list of the dimensions in the order in which they should be looped over"""
    return self._driver.orderedDimensionsForFieldInSpace(self, space)
  
  @lazy_property
  def allocSize(self):
    return '_' + self.name + '_alloc_size'
  
  def sizeInSpace(self, space):
    """Return a name of a variable the value of which is the size of this field in `space`."""
    if not self.isDistributed:
      return self.allocSize
    return self._driver.sizeOfFieldInSpace(self, space)
  
  
  def sortDimensions(self):
    """Sort the dimensions of the field into canonical (geometry element) order."""
    geometryTemplate = self.getVar('geometry')
    sortFunction = lambda x, y: cmp(geometryTemplate.indexOfDimension(x), geometryTemplate.indexOfDimension(y))
    self.dimensions.sort(sortFunction)
  
  def spaceFromString(self, spacesString, xmlElement = None):
    """
    Return the ``space`` bitmask corresponding to `spacesString` for this field.
    
    The contents of `spacesString` must be a sequence of dimension names or fourier
    space versions of those dimension names (i.e. the dimension name prefixed with a 'k')
    where legal.
    
    For example, if the geometry has dimensions 'x', 'y', 'z' and 'u', where 'u' is an
    integer-valued dimension, then the following are valid entries in `spacesString`:
    'x', 'kx', 'y', 'ky', 'z' and 'u'.
    
    Note that the entries in `spacesString` do not need to be in any order.
    """
    resultSpace = 0
    
    xmlElement = xmlElement or self.xmlElement
    
    # Complain if illegal fieldnames or k[integer-valued] are used
    legalDimensionNames = set()
    for fieldDimension in self.dimensions:
      for rep in fieldDimension.representations:
        legalDimensionNames.add(rep.name)
    
    spacesSymbols = RegularExpressionStrings.symbolsInString(spacesString)
    
    for symbol in spacesSymbols:
      if not symbol in legalDimensionNames:
        raise ParserException(xmlElement, 
                "The fourier_space string must only contain real-valued dimensions from the\n"
                "designated field.  '%(symbol)s' cannot be used."  % locals())
    
    for fieldDimension in self.dimensions:
      fieldDimensionName = fieldDimension.name
      validDimensionNamesForField = set([rep.name for rep in fieldDimension.representations])
      
      dimensionOccurrences = sum([spacesSymbols.count(dimName) for dimName in validDimensionNamesForField])
      
      if dimensionOccurrences > 1:
        raise ParserException(xmlElement,
                  "The fourier_space attribute must only have one entry for dimension '%(fieldDimensionName)s'." % locals())
      elif dimensionOccurrences == 0 and fieldDimension.isTransformable:
        raise ParserException(xmlElement,
                  "The fourier_space attribute must have an entry for dimension '%(fieldDimensionName)s'." % locals())
      
      if fieldDimension.isTransformable and spacesSymbols.count(fieldDimension.inSpace(-1).name):
        resultSpace |= fieldDimension.transformMask
    return resultSpace
  
  @classmethod
  def sortedFieldWithDimensionNames(cls, dimensionNames, xmlElement = None, createIfNeeded = True):
    """
    Return a field containing `dimensionNames` as the dimensions in canonical order.
    This function will either return an existing field, or create one if necessary.
    
    Although this class method is defined on `_FieldElement`, it must be called as
    ``FieldElement.sortedFieldWithDimensionNames`` in order to get a FieldElement
    instance out.
    """
    globalNameSpace = cls.argumentsToTemplateConstructors['searchList'][0]
    geometry = globalNameSpace['geometry']
    fields = globalNameSpace['fields']
    
    dimensionNames = list(dimensionNames)
    
    # If we have an xmlElement, first check that all of the dimension names provided
    # are valid dimension names
    if xmlElement:
      for dimensionName in dimensionNames:
        if not geometry.hasDimensionName(dimensionName):
          raise ParserException(xmlElement, "Don't recognise '%(dimensionName)s' as one of "
                                            "the dimensions defined in the geometry element." % locals())
    
    dimensionNames.sort(lambda x, y: cmp(geometry.indexOfDimensionName(x), geometry.indexOfDimensionName(y)))
    
    fieldDimensions = [geometry.dimensionWithName(dimName) for dimName in dimensionNames]
    
    if len(dimensionNames):
      fieldName = ''.join(dimensionNames)
    else:
      fieldName = 'dimensionless'
    
    potentialFields = filter(lambda x: x.dimensions == fieldDimensions and x.name == fieldName, fields)
    
    field = None
    
    if potentialFields:
      # If there is a field already in existence that matches our requirements, use it
      field = potentialFields[0]
    elif createIfNeeded:
      # Otherwise we need to construct our own
      field = cls(name = fieldName, **cls.argumentsToTemplateConstructors)
      # Copy in our dimensions
      field.dimensions[:] = [dim.copy(parent = field) for dim in fieldDimensions]
      
      if xmlElement:
        field.xmlElement = xmlElement
    
    return field
  


