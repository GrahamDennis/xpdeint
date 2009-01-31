#!/usr/bin/env python
# encoding: utf-8
"""
_Dimension.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement
from xpdeint.Utilities import lazy_property
import types

class _Dimension(ScriptElement):
  """
  The idea here is that a dimension represents a given coordinate, 'x' say. And this
  coordinate may have a number of numerical 'representations' in terms of a grid. For
  example, the dimension 'x' may be represented by a uniformly spaced grid. The dimension
  could also be represented in terms of a transformed (e.g. fourier-transformed) coordinate
  'kx' that may also be uniformly spaced, but the in-memory layout of this grid will be
  different. Alternatively, 'x' may be represented by a non-uniformly spaced grid. All of these
  details are handled by the `DimensionRepresentation` classes of which a given dimension is
  permitted to have at most two instances at present. One instance should be the 'untransformed'
  dimension, while the other (if present) is the transformed representation of this dimension.
  In this way, different transforms can create the appropriate representations for a given dimension
  instead of hardcoding the assumption that the untransformed dimension is always uniformly spaced
  and the transformed dimension is always uniformly spaced, but the memory layout is split.
  
  This kind of separation is particularly important for things like Hankel transforms which require
  non-uniformly spaced grids, but will also be useful for discrete cosine/sine transforms which have
  a transformed coordinate that is strictly positive.
  """
  def __init__(self, *args, **KWs):
    localKWs = self.extractLocalKWs(['name', 'transverse','transform', 'aliases'], KWs)
    ScriptElement.__init__(self, *args, **KWs)
    
    self.name = localKWs['name']
    self.transverse = localKWs.get('transverse', True)
    self.transform = localKWs.get('transform')
    self.aliases = localKWs.get('aliases', set())
    self.aliases.add(self.name)
    
    self.representations = []
    self._transformMask = None
    self._mappingRules = None
  
  @property
  def children(self):
    children = super(_Dimension, self).children
    # Only add non-None representations
    children.extend([rep for rep in self.representations if rep])
    return children
  
  @lazy_property
  def prefix(self):
    return self.parent.prefix
  
  @lazy_property
  def isTransformable(self):
    return len(self.representations) >= 2
  
  @lazy_property
  def transformMask(self):
    if self._transformMask == None:
      geometry = self.getVar('geometry')
      self._transformMask = 1 << geometry.indexOfDimension(self)
    return self._transformMask
  
  @lazy_property
  def mappingRules(self):
    if not self.parent:
      return self.transform.mappingRulesForDimensionInField(self, None)
    if not self._mappingRules:
      self._mappingRules = self.transform.mappingRulesForDimensionInField(self, self.parent)
      assert self.mappingRules[-1][0] == None
    return self._mappingRules
  
  def inSpace(self, space):
    if isinstance(space, types.StringTypes):
      # The space is a string, so use a proxy (if necessary)
      # to allow the correct representation to be determined at run-time
      if len(self.representations) == 1:
        return self.representations[0]
      else:
        return RepresentationProxy(space, self.mappingRules, self.representations[:])
    
    # We know the space value now, so just return the correct representation
    for mask, index in self.mappingRules:
      if mask == None:
        return self.representations[index]
      elif (mask & space) == mask:
        return self.representations[index]
  
  def canTransformVector(self, vector):
    return self.transform.canTransformVectorInDimension(vector, self)
  
  def addRepresentation(self, rep):
    self.representations.append(rep)
  
  def invalidateRepresentationsOtherThan(self, mainRep):
    for idx, rep in enumerate(self.representations[:]):
      if id(rep) != id(mainRep):
        if rep: rep.remove()
        self.representations[idx] = None
  
  def invalidateRepresentation(self, oldRep):
    for idx, rep in enumerate(self.representations[:]):
      if id(rep) == id(oldRep):
        if rep: rep.remove()
        self.representations[idx] = None
  
  @lazy_property
  def isDistributed(self):
    return any([rep.hasLocalOffset for rep in self.representations if rep])
  
  def copy(self, parent):
    newInstanceKeys = ['name', 'transverse', 'transform', 'aliases']
    newInstanceDict = dict([(key, getattr(self, key)) for key in newInstanceKeys])
    newInstanceDict.update(self.argumentsToTemplateConstructors)
    newDim = self.__class__(parent = parent, **newInstanceDict)
    for rep in self.representations:
      if rep:
        newRep = rep.copy(parent = newDim)
      else:
        newRep = rep
      newDim.representations.append(newRep)
    return newDim
  
  def __eq__(self, other):
    try:
      return (self.name == other.name and
              self.transverse == other.transverse and
              self.representations == other.representations)
    except AttributeError:
      return NotImplemented
  
  def __ne__(self, other):
    eq = self.__eq__(other)
    if eq is NotImplemented:
      return NotImplemented
    else:
      return not eq
  

class RepresentationProxy(object):
  def __init__(self, spaceVarName, mappingRules, representations):
    object.__init__(self)
    
    self.spaceVarName = spaceVarName
    self.mappingRules = mappingRules
    self.representations = representations
  
  def __getattribute__(self, name):
    """Produce ternary expressions that get the variables in the correct representation."""
    # As we are customising attribute access in this method, attempts to access attributes directly
    # would lead to infinite recursion (bad), so we must access variables specially
    representations = object.__getattribute__(self, 'representations')
    # If not all of the representations have this attribute, then raise an exception
    if not all([hasattr(rep, name) for rep in representations]):
      raise AttributeError
    
    result = []
    resultIndex = 0
    mappingRules = object.__getattribute__(self, 'mappingRules')
    spaceVarName = object.__getattribute__(self, 'spaceVarName')
    for mask, index in mappingRules:
      if mask != None:
        result.insert(resultIndex, '( (%(spaceVarName)s & %(mask)i) == %(mask)i ? ' % locals())
        resultIndex += 1
        result.insert(resultIndex+1, ')')
      representationValue = getattr(representations[index], name)
      if not isinstance(representationValue, types.StringTypes):
        raise AttributeError
      result.insert(resultIndex, representationValue)
      resultIndex += 1
      if mask != None:
        result.insert(resultIndex, ' : ')
        resultIndex += 1
      
    return ''.join(result)
  

