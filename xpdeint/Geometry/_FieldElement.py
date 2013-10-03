#!/usr/bin/env python
# encoding: utf-8
"""
_FieldElement.py

This contains all the pure-python code for FieldElement.tmpl

Created by Graham Dennis on 2007-10-17.

Copyright (c) 2007-2012, Graham Dennis

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

from xpdeint.ScriptElement import ScriptElement

from xpdeint.ParserException import ParserException, parserWarning

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
  
  @lazy_property
  def prefix(self):
    return '_' + self.name if not self.name is 'geometry' else ''
  
  # Do we have the dimension?
  def hasDimension(self, dimension):
    return self.hasDimensionName(dimension.name)
  
  # Do we have a dimension matching dimensionName?
  def hasDimensionName(self, dimensionName):
    dimensionList = filter(lambda x: x.name == dimensionName, self.dimensions)
    assert len(dimensionList) <= 1
    
    return len(dimensionList) == 1
  
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
  
  def localPointsInDimensionsAfterDimRepInBasis(self, dimRep, basis):
    dimReps = self.inBasis(basis)
    # Grab everything after dimension
    dimReps = dimReps[(dimReps.index(dimRep)+1):]
    if not len(dimReps):
      return '1'
    return ' * '.join([dimRep.localLattice for dimRep in dimReps])
  
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
  
  @lazy_property
  def isDistributed(self):
    return self._driver.isFieldDistributed(self)
  
  def sizeInBasis(self, basis):
    return '(' + (' * '.join([dimRep.localLattice for dimRep in self.inBasis(basis)]) or '1') + ')'
  
  def sortDimensions(self):
    """Sort the dimensions of the field into canonical (geometry element) order."""
    geometryTemplate = self.getVar('geometry')
    sortFunction = lambda x, y: cmp(geometryTemplate.indexOfDimension(x), geometryTemplate.indexOfDimension(y))
    self.dimensions.sort(sortFunction)
  
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
      dimRepNames = set([dr.canonicalName for dim in self.dimensions for dr in geometry.dimensionWithName(dim.name).representations])
      if not len(dimRepNames.intersection(basis)) == len(self.dimensions):
        raise ParserException(
          None,
          "Internal error: The basis provided (%s) contained insufficient information to generate the appropriate basis for a vector in this field (%s). A specification is required for all dimensions (%s). \n\nPlease report this error to %s." %
          (', '.join(basis), self.name, ', '.join(dim.name for dim in self.dimensions), self.getVar('bugReportAddress'))
        )
      newBasis = tuple(b for b in basis if b in dimRepNames)
      maxDistributedIdx = max([idx for idx, dimRepName in enumerate(newBasis) if dimRepName.startswith('distributed ')] + [-1])
      orderedDimRepNames = [(idx, dimRep.canonicalName) 
                                for idx, dim in enumerate(self.dimensions) 
                                  for dimRep in geometry.dimensionWithName(dim.name).representations
                                    if dimRep.canonicalName in newBasis[maxDistributedIdx+1:]]
      orderedDimRepNames.sort()
      newBasis = self._driver.canonicalBasisForBasis(newBasis[:maxDistributedIdx+1] + tuple([x[1] for x in orderedDimRepNames]))
      self._basisForBasisCache[basis] = newBasis
    return self._basisForBasisCache[basis]
  
  def completedBasisForBasis(self, basis, defaultBasis):
    # If an incomplete basis is known for this field, it may be desirable to complete the basis using information from a default.
    basis = basis or ()
    geometry = self.getVar('geometry')
    dimRepNameToDimMap = dict((dr.canonicalName, dim) for dim in self.dimensions for dr in geometry.dimensionWithName(dim.name).representations)
    missingDimensions = set(self.dimensions)
    for dimRepName in basis:
      missingDimensions.discard(dimRepNameToDimMap.get(dimRepName))
    # We now have the missing dimensions, now to find the corresponding dimRepName from the field's defaultCoordinateBasis
    for dimRepName in defaultBasis:
      dimension = dimRepNameToDimMap[dimRepName]
      if dimension in missingDimensions:
        missingDimensions.discard(dimension)
        basis += (dimRepName,)
    orderedBasis = tuple(dim.inBasis(basis).name for dim in self.dimensions)
    canonicalBasis = self._driver.canonicalBasisForBasis(orderedBasis)
    return self.basisForBasis(canonicalBasis)
  
  def inBasis(self, basis):
    """
    Return a list of dimReps corresponding to the supplied basis. We cannot guarantee that the basis we are passed is directly appropriate
    for this field. So we must pass it through basisForBasis.
    """
    basis = self.basisForBasis(basis)
    dimRepNameMap = dict([(dimRep.canonicalName, dimRep) for dim in self.dimensions for dimRep in dim.representations if dimRep])
    return [dimRepNameMap[b] for b in basis]
  
  def basisFromString(self, basisString, xmlElement = None):
    """
    Return the basis given `basisString`.
    """
    xmlElement = xmlElement or self.xmlElement
    
    basis = set(symbolsInString(basisString, xmlElement = xmlElement))
    
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
  
  @lazy_property
  def defaultCoordinateBasis(self):
    # Grab the first rep for each dim whose tag is a 'coordinate' tag
    # i.e. the tag is a subclass of the 'coordinate' tag.
    return self._driver.canonicalBasisForBasis(
      tuple([dim.firstDimRepWithTagName('coordinate').canonicalName for dim in self.dimensions])
    )
  
  @lazy_property
  def defaultSpectralBasis(self):
    # Grab the first dim rep for each dim whose tag is 'spectral' if one exists
    # Failing that, take the first one with a 'coordinate' tag.
    reps = []
    for dim in self.dimensions:
      for tagName in ['spectral', 'coordinate']:
        rep = dim.firstDimRepWithTagName(tagName)
        if rep: break
      assert rep, "We should have found a representation that was either spectral or coordinate but somehow failed"
      reps.append(rep.canonicalName)
    return self._driver.canonicalBasisForBasis(tuple(reps))
  
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
  


