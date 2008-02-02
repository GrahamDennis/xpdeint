#!/usr/bin/env python
# encoding: utf-8
"""
_ErrorCheckFeature.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from _Feature import _Feature

class _ErrorCheckFeature (_Feature):
  def canRunPreflightYet(self):
    features = self.getVar('features')
    if  'Stochastic' in features:
      stochasticFeature = features['Stochastic']
      for noise in stochasticFeature.noises:
        if not hasattr(noise, 'noiseVectors'):
          return False
    
    return super(_ErrorCheckFeature, self).canRunPreflightYet()
  
  
  def preflight(self):
    for mg in self.getVar('momentGroups'):
      mg.processedVector.aliases.add('_%s_halfstep' % mg.outputField.name)
    
    self.noiseAliases = []
    features = self.getVar('features')
    if 'Stochastic' in features:
      stochasticFeature = features['Stochastic']
      for noise in stochasticFeature.noises:
        for noiseVector in noise.noiseVectors.itervalues():
          noiseVector.aliases.add('_%s2' % noiseVector.id)
          self.noiseAliases.append(noiseVector)
    
    super(_ErrorCheckFeature, self).preflight()
  
