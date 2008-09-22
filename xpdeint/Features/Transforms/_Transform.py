#!/usr/bin/env python
# encoding: utf-8
"""
_Transform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature
from xpdeint.Utilities import lazyproperty
import operator

class _Transform (_Feature):
  mpiCapableSubclass = None
  
  def __init__(self, *args, **KWs):
    _Feature.__init__(self, *args, **KWs)
    self.transformMask = 0
  
  @lazyproperty
  def isMPICapable(self):
    return bool(self.mpiCapableSubclass)
  
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
  
  def preflight(self):
    self.transformMask = reduce(operator.__or__, [d.transformMask for d in self.getVar('geometry').dimensions if d.transform == self], 0)
  

