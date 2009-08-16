#!/usr/bin/env python
# encoding: utf-8
"""
_Transform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement
from xpdeint.Geometry._Dimension import _Dimension
from xpdeint.Utilities import lazy_property
import operator

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
                   type = 'real', xmlElement = None):
    dim = _Dimension(name = name, transform = self, aliases = aliases, parent = parent, xmlElement = xmlElement,
                     **self.argumentsToTemplateConstructors)
    return dim
  
  def setVectorAllocSizes(self, vectors):
    return ''
  

