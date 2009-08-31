#!/usr/bin/env python
# encoding: utf-8
"""
_ErrorCheck.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature
from xpdeint.Vectors.NoiseVector import NoiseVector

class _ErrorCheck (_Feature):
  
  def preflight(self):
    super(_ErrorCheck, self).preflight()
    
    for mg in self.getVar('momentGroups'):
      mg.processedVector.aliases.add('_%s_halfstep' % mg.outputField.name)
    
    for noiseVector in [o for o in self.getVar('templates') if isinstance(o, NoiseVector)]:
      if not noiseVector.static:
        noiseVector.aliases.add('_%s2' % noiseVector.id)
      
