#!/usr/bin/env python
# encoding: utf-8
"""
_DimensionRepresentation.py

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

from xpdeint.ScriptElement import ScriptElement
from xpdeint.Utilities import lazy_property

class _DimensionRepresentation(ScriptElement):
  """
  See the documentation for the `_Dimension` class for more details, but the idea here is that
  the details of the geometry of a dimension in a given space are controlled by a dimension
  'representation'. This class controls the creation of loops over the dimension, the creation
  of variables for the lattice, minimum and maximum of the representation. Further things like
  how exactly to split the dimension are controlled by the transform that created the representation.
  """
  
  class ReductionMethod(object):
    fixedRange = 0
    fixedStep = 1
    
    @staticmethod
    def validate(method):
      return method in range(2)
  
  tags = {}
  
  # We define two lattice attributes: latticeEstimate and runtimeLattice.
  # If the size of the geometry lattice is a number specified in the XMDS script, 
  # both "latticeEstimate" and "runtimeLattice" are set to this value. If the size is undefined
  # at parse time and specified at run time, "runtimeLattice" holds a string which is
  # the C-code global variable that will give the lattice size at run time, and
  # "latticeEstimate" is set to a sane numeric placeholder (e.g. 128) for parsing purposes.
  
  instanceAttributes = ['name',  'type', 'runtimeLattice', '_localVariablePrefix', 'reductionMethod', 'tag']
  
  instanceDefaults = dict(
    runtimeLattice = 0,
    reductionMethod = ReductionMethod.fixedRange,
    tag = -1
  )
  
  @classmethod
  def registerTag(cls, tagName, parent = None):
    parent = cls.tagForName(parent) if parent else object
    tag = type(tagName, (parent,), {'tagName': tagName})
    return cls.tags.setdefault(tagName, tag)
  
  @classmethod
  def tagForName(cls, tagName):
    return cls.tags[tagName]
  
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(self.combinedClassInfo('instanceAttributes'), KWs)
    ScriptElement.__init__(self, **KWs)
    
    instanceDefaults = self.combinedClassInfo('instanceDefaults')
    [setattr(self, attrName, localKWs[attrName] if attrName in localKWs else instanceDefaults.get(attrName))
      for attrName in self.combinedClassInfo('instanceAttributes')]
    
    self.silent = False
  
  def __eq__(self, other):
    try:
      return all([getattr(self, attrName) == getattr(other, attrName) for attrName in self.combinedClassInfo('instanceAttributes')])
    except AttributeError:
      return NotImplemented
  
  def __ne__(self, other):
    eq = self.__eq__(other)
    if eq is NotImplemented:
      return NotImplemented
    else:
      return not eq
  
  def combinedClassInfo(self, attrName):
    attributeType = type(getattr(self, attrName))
    result = {list: set}.get(attributeType, attributeType)()
    [result.update(getattr(cls, attrName)) for cls in reversed(type(self).mro()) if hasattr(cls, attrName)]
    return result
  
  def copy(self, parent):
    newInstanceDict = dict([(attrName, getattr(self, attrName)) for attrName in self.combinedClassInfo('instanceAttributes')])
    newInstanceDict.update(self.argumentsToTemplateConstructors)
    return type(self)(parent = parent, **newInstanceDict)
  
  @lazy_property
  def prefix(self):
    return self.parent.prefix
  
  @lazy_property
  def canonicalName(self):
    return self.name if not self.hasLocalOffset else 'distributed ' + self.name
  
  @lazy_property
  def globalLattice(self):
    return self.prefix + '_lattice_' + self.name
  
  def setHasLocalOffset(self, localVariablePrefix = ''):
    if localVariablePrefix == None:
      self._localVariablePrefix = None
    else:
      self._localVariablePrefix = '_local'
      if localVariablePrefix:
        self._localVariablePrefix += '_' + localVariablePrefix
    if 'hasLocalOffset' in self.__dict__:
      del self.hasLocalOffset
  
  @lazy_property
  def hasLocalOffset(self):
    return self._localVariablePrefix != None
  
  @lazy_property
  def localLattice(self):
    if not self.hasLocalOffset:
      return self.globalLattice
    else:
      return self.prefix + self._localVariablePrefix + '_lattice_' + self.name
  
  @lazy_property
  def localOffset(self):
    if not self.hasLocalOffset:
      return '0'
    else:
      return self.prefix + self._localVariablePrefix + '_offset_' + self.name
  
  @lazy_property
  def minimum(self):
    return self.prefix + '_min_' + self.name
  
  @lazy_property
  def maximum(self):
    return self.prefix + '_max_' + self.name
  
  @lazy_property
  def arrayName(self):
    return self.prefix + '_' + self.name
  
  @lazy_property
  def stepSize(self):
    return self.prefix + '_d' + self.name
  
  @lazy_property
  def loopIndex(self):
    return '_index_' + self.name
  
  @property
  def volumePrefactor(self):
      return self.parent.volumePrefactor
  
  @property
  def latticeEstimate(self):
    # Note this will always be a number, even if runtimeLattice is a string
    if isinstance(self.runtimeLattice, basestring):
      return 128
    else:
      return self.runtimeLattice


  def aliasRepresentationsForFieldInBasis(self, field, basis):
    return set([field.dimensionWithName(aliasName).inBasis(basis) \
                for aliasName in self.parent.aliases if field.hasDimensionName(aliasName)])
  
  def nonlocalAccessIndexFromStringForFieldInBasis(self, accessString, field, basis):
    """
    Return the string representing the index to be used for this dimension representation
    when accessing it nonlocally with the string `accessString` and when looping over
    `field` in `basis`.
    """
    # If we don't have any dimension aliases, then our subclasses will have to handle
    # any other cases for nonlocal dimension access
    if not len(self.parent.aliases) > 1: return
    
    aliasRepresentations = self.aliasRepresentationsForFieldInBasis(field, basis)
    matchingAliasReps = [rep for rep in aliasRepresentations if rep.name == accessString]
    if not matchingAliasReps: return
    matchingAliasRep = matchingAliasReps[0]
    # We are the dimRep for the vector being accessed nonlocally.  
    # We need to return the index not in us, but in the corresponding dimRep in field (which is the looping field)
    fieldDimRep = field.dimensionWithName(self.parent.name).inBasis(basis)
    return fieldDimRep.localIndexFromIndexForDimensionRep(matchingAliasRep)
    
  

_DimensionRepresentation.registerTag('coordinate')
_DimensionRepresentation.registerTag('spectral')
_DimensionRepresentation.registerTag('auxiliary')
