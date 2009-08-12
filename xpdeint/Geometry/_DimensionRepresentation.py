#!/usr/bin/env python
# encoding: utf-8
"""
_DimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
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
  
  tags = {}
  
  instanceAttributes = ['name',  'type', 'lattice', '_localVariablePrefix', 'reductionMethod', 'tag']
  
  instanceDefaults = dict(
    lattice = 0,
    reductionMethod = -1,
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
    # We cannot access a dim rep nonlocally with an alias that is distributed.
    if matchingAliasRep.hasLocalOffset: return
    return matchingAliasRep.loopIndex
    
  

_DimensionRepresentation.registerTag('coordinate')
_DimensionRepresentation.registerTag('spectral')
_DimensionRepresentation.registerTag('auxiliary')
