#!/usr/bin/env python
# encoding: utf-8
"""
_Transform.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature

class _Transform (_Feature):
  mpiCapableSubclass = None
  
  @property
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
  
