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
    self.transformMask = 0
  
  def __hash__(self):
    """
    Returns a hash of the transform.
    This is used to ensure the ordering of transforms in sets remains the same between invocations.
    """
    return hash(self.transformName)
  
  @lazy_property
  def isMPICapable(self):
    return bool(self.mpiCapableSubclass)
  
  def transformMaskForVector(self, vector):
    return reduce(operator.__or__, [d.transformMask for d in vector.field.dimensions if d.transform == self], 0)
  
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
  
  def canTransformVectorInDimension(self, vector, dim):
    if dim.isTransformable:
      return True
    else:
      return False
  
  def mappingRulesForDimensionInField(self, dim, field):
    """
    Return default mapping rules. Each rule is a ``(mask, index)`` pair.
    A mapping rule matches a space if ``mask & space`` is nonzero. The rules
    are tried in order until one matches, and the representation correponding
    to the index in the rule is the result.
    """
    return [(dim.transformMask, 1), (None, 0)]
  
  def newDimension(self, name, lattice, minimum, maximum,
                   parent, transformName, aliases = set(),
                   type = 'real', xmlElement = None):
    dim = _Dimension(name = name, transform = self, aliases = aliases, parent = parent, xmlElement = xmlElement,
                     **self.argumentsToTemplateConstructors)
    return dim
  
  
  def preflight(self):
    super(_Transform, self).preflight()
    self.transformMask = reduce(operator.__or__, [d.transformMask for d in self.getVar('geometry').dimensions if d.transform == self], 0)
  

