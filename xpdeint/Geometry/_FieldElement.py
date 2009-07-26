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
from xpdeint.ParserException import ParserException, parserWarning
from xpdeint.Geometry.NonUniformDimensionRepresentation import NonUniformDimensionRepresentation

from xpdeint.Utilities import lazy_property, symbolsInString

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
    self._basisForBasisCache = {}
    
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
    result = []
    for rep in [rep for rep in reps if rep.type == 'real']:
      if isinstance(rep, NonUniformDimensionRepresentation):
        parserWarning(
          self.xmlElement,
          "You're asking for a noise for a non-uniform dimension. "
          "If you don't know how to handle this, treat this as an error."
        )
        continue
      result.append(rep.stepSize)
    if not result:
        return '1.0'
    return '(' + ' * '.join(result) + ')'
  
  @lazy_property
  def isDistributed(self):
    return self._driver.isFieldDistributed(self)
  
  def orderedDimensionsInSpace(self, space):
    """Return a list of the dimensions in the order in which they should be looped over"""
    return self._driver.orderedDimensionsForFieldInSpace(self, space)
  
  @lazy_property
  def size(self):
    return '_' + self.name + '_size'
  
  @lazy_property
  def allocSize(self):
    if not self.isDistributed:
      return self.size
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
    
    spacesSymbols = symbolsInString(spacesString, xmlElement = xmlElement)
    
    for symbol in spacesSymbols:
      if not symbol in legalDimensionNames:
        raise ParserException(xmlElement, 
                "'%(symbol)s' is not recognised as a dimension name for this field."  % locals())
    
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
  
  def basisForBasis(self, basis):
    """
    Return a basis that only contains the dimensions in this field.
    It also handles the case in which a distributed basis becomes a non-distributed basis
    after a dimension has been omitted.
    We do not validate that such a transformation is possible.
    
    The results of this method are cached on a per-instance basis for speed.
    """
    if not basis in self._basisForBasisCache:
      geometry = self.getVar('geometry')
      dimRepNames = [dr.canonicalName for dim in self.dimensions for dr in geometry.dimensionWithName(dim.name).representations]
      if not len(dimRepNames.intersection(basis)) == len(self.dimensions):
        raise ParserException(
          self.xmlElement,
          "Internal error: The basis provided (%s) contained insufficient information to generate the appropriate basis for a vector in this field (%s)." %
          (', '.join(basis), self.name)
        )
      
      newBasis = self._driver.canonicalBasisForBasis(tuple(b for b in basis if b in dimRepNames))
      self._basisForBasisCache[basis] = newBasis
    return self._basisForBasisCache[basis]
  
  def inBasis(self, basis):
    """
    Return a list of dimReps corresponding to the supplied basis. We cannot guarantee that the basis we are passed is directly appropriate
    for this field. So we must pass it through basisForBasis.
    """
    
    basis = self.basisForBasis(basis)
    dimRepNameMap = dict([(dimRep.canonicalName, dimRep) for dim in self.dimensions for dimRep in dim.representations])
    return [dimRepNameMap[b] for b in basis]
  
  def basisFromString(self, basisString, xmlElement = None):
    """
    Return the basis given `spacesString`.
    """
    xmlElement = xmlElement or self.xmlElement
    
    basis = set(symbolsInString(spacesString, xmlElement = xmlElement))
    
    geometry = self.getVar('geometry')
    validNames = set([dimRep.name for dim in self.dimensions for dimRep in geometry.dimensionWithName(dim.name).representations])
    if basis.difference(validNames):
      raise ParserException(
        xmlElement,
        "The following names are not valid basis specifiers: %s." % ', '.join(basis.difference(validNames))
      )
    # Now we know we don't have any specifiers that we can't identify, 
    # so we just need to check that we don't have two specifiers for the same dimension.
    dimToDimRepMap = dict([(dim.name, [dimRep.name for dimRep in geometry.dimensionWithName(dim.name).representations]) for dim in self.dimensions])
    
    for dimName, dimRepNames in dimToDimRepMap.items():
      basisNamesInDimRepNames = basis.intersection(dimRepNames)
      if len(basisNamesInDimRepNames) > 1:
        raise ParserException(
          xmlElement,
          "There is more than one basis specifier for dimension '%s'. The conflict is between %s." \
            % (dimName, ' and '.join(basis.intersection(dimRepNames)))
        )
      elif len(basisNamesInDimRepNames) == 1:
        # Use the map to now list the actual chosen dimRep name
        dimToDimRepMap[dimName] = list(basisNamesInDimRepNames)[0]
      else:
        # This dimension doesn't have a rep specified. Default to the first rep.
        dimToDimRepMap[dimName] = dimRepNames[0]
      if dimToDimRepMap[dimName] is None:
        raise ParserException(
          xmlElement,
          "Internal Error: When turning string '%s' into a basis, we were unable to determine the correct dimension representation for the %s dimension. "
          "Please report this error to %s" \
            % (basisString, dimName, self.getVar('bugReportAddress'))
        )
    
    # Now we just need to construct the basis
    
    basis = self._driver.canonicalBasisForBasis(tuple(dimToDimRepMap[dim.name] for dim in self.dimensions))
    
    return basis
  
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
  


