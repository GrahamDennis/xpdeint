#!/usr/bin/env python
# encoding: utf-8
"""
_Dimension.py

Created by Graham Dennis on 2008-02-02.

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
    localKWs = self.extractLocalKWs(['name', 'transverse','transform', 'aliases', 'volumePrefactor'], KWs)
    ScriptElement.__init__(self, *args, **KWs)
    
    self.name = localKWs['name']
    self.transverse = localKWs.get('transverse', True)
    self.transform = localKWs.get('transform')
    self.aliases = localKWs.get('aliases', set())
    self.aliases.add(self.name)
    self.volumePrefactor = localKWs.get('volumePrefactor')
    self.volumePrefactor = self.volumePrefactor if self.volumePrefactor else '1.0'
    
    self.representations = []
  
  def preflight(self):
    # FIXME: DODGY. When we go to the 'basis' concept from the 'spaces' concept, this should go away
    basisNameMap = dict([(rep.name, set()) for rep in self.representations if rep])
    for rep in [rep for rep in self.representations if rep]:
      basisNameMap[rep.name].add(rep)
    for repName, repSet in basisNameMap.iteritems():
      if len(repSet) > 1:
        for rep in [rep for rep in repSet if not rep.hasLocalOffset]:
          rep.silent = True
  
  @lazy_property
  def prefix(self):
    return self.parent.prefix
  
  @lazy_property
  def isTransformable(self):
    return len(self.representations) >= 2
  
  def inBasis(self, basis):
    for rep in self.representations:
      if rep and rep.canonicalName in basis: return rep
    assert False
  
  def addRepresentation(self, rep):
    self.representations.append(rep)
    self._children.append(rep)
  
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
  
  def setReducedLatticeInBasis(self, newLattice, basis):
    dimRep = self.inBasis(basis)
    reductionMethod = dimRep.reductionMethod
    assert dimRep.ReductionMethod.validate(reductionMethod)
    if dimRep.runtimeLattice == newLattice: return
    newDimRep = dimRep.copy(parent = self)
    newDimRep.runtimeLattice = newLattice
    self._children.append(newDimRep)
    self.representations[self.representations.index(dimRep)] = newDimRep
    self.invalidateRepresentationsOtherThan(newDimRep)
  
  def firstDimRepWithTagName(self, tagName):
    repList = [rep for rep in self.representations if rep and issubclass(rep.tag, rep.tagForName(tagName))]
    return repList[0] if repList else None
  
  @lazy_property
  def isDistributed(self):
    return any([rep.hasLocalOffset for rep in self.representations if rep])
  
  def copy(self, parent):
    newInstanceKeys = ['name', 'transverse', 'transform', 'aliases']
    newInstanceDict = dict([(key, getattr(self, key)) for key in newInstanceKeys])
    newInstanceDict.update(self.argumentsToTemplateConstructors)
    newDim = self.__class__(parent = parent, **newInstanceDict)
    newDim.representations = self.representations[:]
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
  
