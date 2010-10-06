#!/usr/bin/env python
# encoding: utf-8
"""
_Stochastic.py

Created by Graham Dennis on 2008-01-13.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature
from xpdeint.Vectors.NoiseVector import NoiseVector
from xpdeint.Segments.Integrators.AdaptiveStep import AdaptiveStep as AdaptiveStepIntegrator

from xpdeint.ParserException import ParserException, parserWarning

class _Stochastic (_Feature):
  def adaptiveIntegratorsWithNoises(self):
    adaptiveIntegratorList = [ai for ai in self.getVar('templates') if isinstance(ai, AdaptiveStepIntegrator) and ai.dynamicNoiseVectors]

    return adaptiveIntegratorList

  def xsilOutputInfo(self, dict):
    return self.implementationsForChildren('xsilOutputInfo', dict)
  
  def preflight(self):
    super(_Stochastic, self).preflight()
    
    self.noiseVectors = [o for o in self.getVar('templates') if isinstance(o, NoiseVector)]
    
    # For each adaptive step integrator using noises, we need to reduce the order of the integrator
    for integrator in [ai for ai in self.getVar('templates') if isinstance(ai, AdaptiveStepIntegrator) and ai.dynamicNoiseVectors]:
      integrator.stepper.integrationOrder /= 2.0
    
    
  
