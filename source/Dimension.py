#!/usr/bin/env python
# encoding: utf-8
"""
Dimension.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

class Dimension(object):
  def __init__(self, name, transverse, **KWs):
    self.name = name
    self.transverse = transverse
    
    self.lattice = KWs.get('lattice', 0)
    self.minimum = KWs.get('minimum', 0.0)
    self.maximum = KWs.get('maximum', 1.0)
    self.type = KWs.get('type', 'double')
    if 'override' in KWs:
      self.override = KWs['override']
  
  
  def getFourier(self):
    if self.type == 'long':
      return False
    else:
      if hasattr(self, '_fourierOverride'):
        return self._fourierOverride
      return True
  
  def setFourier(self, value):
    self._fourierOverride = value
  
  fourier = property(getFourier, setFourier)
  
  def copy(self):
    dimension = Dimension(name = self.name, transverse = self.transverse, 
                          lattice = self.lattice, minimum = self.minimum,
                          maximum = self.maximum, type = self.type)
    if hasattr(self, '_fourierOverride'):
      dimension._fourierOverride = self._fourierOverride
    if hasattr(self, 'override'):
      dimension.override = self.override
    
    return dimension
