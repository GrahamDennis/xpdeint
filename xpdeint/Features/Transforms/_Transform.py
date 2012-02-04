#!/usr/bin/env python
# encoding: utf-8
"""
_Transform.py

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
from xpdeint.Geometry._Dimension import _Dimension
from xpdeint.Utilities import lazy_property

class _Transform (ScriptElement):
  mpiCapableSubclass = None
  
  def __init__(self, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    # Register ourselves with the transform multiplexer
    self.getVar('features')['TransformMultiplexer'].transforms.add(self)
    self.transformations = []
  
  def __hash__(self):
    """
    Returns a hash of the transform.
    This is used to ensure the ordering of transforms in sets remains the same between invocations.
    """
    return hash(self.transformName)
  
  @lazy_property
  def isMPICapable(self):
    return bool(self.mpiCapableSubclass)
  
  @property
  def vectorsNeedingThisTransform(self):
    vectors = set()
    for f in self.getVar('fields'): vectors.update(f.vectors)
    return set([v for v in vectors if v.needsTransforms and any([d.transform == self for d in v.field.dimensions])])
  
  def initialiseForMPIWithDimensions(self, dimensions):
    """Upgrade the current class to support MPI."""
    assert self.isMPICapable
    assert not self.__class__ == self.mpiCapableSubclass
    self.__class__ = self.mpiCapableSubclass
    self._driver.distributedTransform = self
    # MPI subclass must define this method
    self.initialiseForMPIWithDimensions(dimensions)
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   type = 'real', volumePrefactor = None, xmlElement = None):
    dim = _Dimension(name = name, transform = self, aliases = aliases, volumePrefactor = volumePrefactor,
                     parent = parent, xmlElement = xmlElement,
                     **self.argumentsToTemplateConstructors)
    return dim
  
  def setVectorAllocSizes(self, vectors):
    return ''
  

