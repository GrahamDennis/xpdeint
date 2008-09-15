#!/usr/bin/env python
# encoding: utf-8
"""
_NonUniformDimensionRepresentation.py

Created by Graham Dennis on 2008-07-30.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation
from xpdeint.Utilities import lazyproperty

class _NonUniformDimensionRepresentation(DimensionRepresentation):
  @lazyproperty
  def index(self):
    return self.prefix + '_index_' + self.name
  
  @lazyproperty
  def arrayName(self):
    return self.prefix + '_' + self.name
  
  def openLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.openLoopAscending()
    else:
      raise NotImplemented
  
  def closeLoop(self, loopingOrder):
    if loopingOrder in [self.LoopingOrder.MemoryOrder, self.LoopingOrder.StrictlyAscendingOrder]:
      return self.closeLoopAscending()
    else:
      raise NotImplemented
  

