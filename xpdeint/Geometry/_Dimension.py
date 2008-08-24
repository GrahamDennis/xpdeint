#!/usr/bin/env python
# encoding: utf-8
"""
_Dimension.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

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
    localKWs = self.extractLocalKWs(['name', 'transverse', 'indexable', 'transform'], KWs)
    ScriptElement.__init__(self, *args, **KWs)
    
    self.name = localKWs['name']
    self.transverse = localKWs.get('transverse', True)
    self.transform = localKWs.get('transform')
    self.indexable = localKWs.get('indexable', False)
    
    self.representations = []
    self._transformMask = None
  
  @property
  def children(self):
    # Only return non-None representations
    return [rep for rep in self.representations if rep]
  
  @property
  def prefix(self):
    return self.parent.prefix
  
  @property
  def isTransformable(self):
    return len(self.representations) == 2
  
  @property
  def transformMask(self):
    if self._transformMask == None:
      geometry = self.getVar('geometry')
      self._transformMask = 1 << geometry.indexOfDimension(self)
    return self._transformMask
  
  def inSpace(self, space):
    # The transform can override this mapping
    if hasattr(self.transform, 'representationForDimensionInSpace'):
      return self.transform.representationForDimensionInSpace(self, space)
    
    index = self.transformMask & space
    if index:
      index = 1
    return self.representations[index]
  
  def canTransformVector(self, vector):
    return self.transform.canTransformVectorInDimension(vector, self)
  
  def addRepresentation(self, rep):
    self.representations.append(rep)
  
  def invalidateRepresentationsOtherThan(self, mainRep):
    for idx, rep in enumerate(self.representations[:]):
      if rep != mainRep:
        rep.remove()
        self.representations[idx] = None
  
  def copy(self, parent = None):
    newInstanceKeys = ['name', 'transverse', 'transform', 'indexable']
    newInstanceDict = dict([(key, getattr(self, key)) for key in newInstanceKeys])
    newInstanceDict.update(self.argumentsToTemplateConstructors)
    newDim = self.__class__(**newInstanceDict)
    for rep in self.representations:
      if rep:
        newRep = rep.copy()
        newRep._parent = newDim
      else:
        newRep = rep
      newDim.representations.append(newRep)
    if parent:
      newDim._parent = parent
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
  

