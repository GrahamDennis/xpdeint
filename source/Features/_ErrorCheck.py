#!/usr/bin/env python
# encoding: utf-8
"""
_ErrorCheck.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from _Feature import _Feature

class _ErrorCheck (_Feature):
  
  def preflight(self):
    super(_ErrorCheck, self).preflight()
    
    for mg in self.getVar('momentGroups'):
      mg.processedVector.aliases.add('_%s_halfstep' % mg.outputField.name)
    
  
