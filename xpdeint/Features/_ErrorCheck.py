#!/usr/bin/env python
# encoding: utf-8
"""
_ErrorCheck.py

Created by Graham Dennis on 2008-02-02.

Copyright (c) 2008-2012, Graham Dennis

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

from xpdeint.Segments.Integrators.FixedStep import FixedStep
from xpdeint.Operators.DeltaAOperator import DeltaAOperator
from xpdeint.Vectors.NoiseVector import NoiseVector

class _ErrorCheck (_Feature):
  
  def post_preflight(self):
    super(_ErrorCheck, self).preflight()
    
    for mg in self.getVar('momentGroups'):
      mg.processedVector.aliases.add('_%s_halfstep' % mg.outputField.name)
    
    # When we have error checking, every dynamic noise vector used by an integrator in a fixed step integrator
    # needs a '2' noise vector alias for generating two half-step noises and adding them.
    if 'ErrorCheck' in self.getVar('features'):
      noiseVectorsNeedingAlias = set()
      # Loop over all fixed-step integrators ...
      for fixedStepIntegrator in [o for o in self.getVar('templates') if isinstance(o, FixedStep)]:
        # ... adding the dynamic noise vectors of that integrator
        noiseVectorsNeedingAlias.update(fixedStepIntegrator.dynamicNoiseVectors)
        
      for noiseVector in noiseVectorsNeedingAlias:
        noiseVector.aliases.add('_%s2' % noiseVector.id)
    
