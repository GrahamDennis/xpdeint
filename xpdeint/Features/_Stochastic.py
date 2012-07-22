#!/usr/bin/env python
# encoding: utf-8
"""
_Stochastic.py

Created by Graham Dennis on 2008-01-13.

Copyright (c) 2008-2012, Graham Dennis and Joe Hope

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from xpdeint.Features._Feature import _Feature
from xpdeint.Vectors.NoiseVector import NoiseVector
from xpdeint.Segments.Integrators.AdaptiveStep import AdaptiveStep as AdaptiveStepIntegrator
from xpdeint.Geometry.NonUniformDimensionRepresentation import NonUniformDimensionRepresentation
from xpdeint.Stochastic.RandomVariables.GaussianRandomVariable import GaussianRandomVariable

from xpdeint.ParserException import ParserException, parserWarning

class _Stochastic (_Feature):
  def adaptiveIntegratorsWithNoises(self):
    adaptiveIntegratorList = [ai for ai in self.getVar('templates') if isinstance(ai, AdaptiveStepIntegrator) and ai.dynamicNoiseVectors]

    return adaptiveIntegratorList

  def xsilOutputInfo(self, dict):
    return '\n'.join(nv.implementationsForFunctionName('xsilOutputInfo', dict) for nv in self.noiseVectors)
  
  def preflight(self):
    super(_Stochastic, self).preflight()
    
    self.noiseVectors = [o for o in self.getVar('templates') if isinstance(o, NoiseVector)]
    
    self.nonUniformDimRepsNeededForGaussianNoise = set()
    for nv in [nv for nv in self.noiseVectors if isinstance(nv.randomVariable, GaussianRandomVariable)]:
      self.nonUniformDimRepsNeededForGaussianNoise.update(dimRep for dimRep in nv.field.inBasis(nv.initialBasis) if isinstance(dimRep, NonUniformDimensionRepresentation))
    
    
  
