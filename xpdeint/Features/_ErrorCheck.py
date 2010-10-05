#!/usr/bin/env python
# encoding: utf-8
"""
_ErrorCheck.py

Created by Graham Dennis on 2008-02-02.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature

from xpdeint.Segments.Integrators.FixedStep import FixedStep
from xpdeint.Operators.DeltaAOperator import DeltaAOperator
from xpdeint.Vectors.NoiseVector import NoiseVector

class _ErrorCheck (_Feature):
  
  def preflight(self):
    super(_ErrorCheck, self).preflight()
    
    for mg in self.getVar('momentGroups'):
      mg.processedVector.aliases.add('_%s_halfstep' % mg.outputField.name)
    
    # When we have error checking, every noise vector used by a delta a operator in a fixed step integrator
    # needs a '2' noise vector alias for generating two half-step noises and adding them.
    if 'ErrorCheck' in self.getVar('features'):
      noiseVectorsNeedingAlias = set()
      # Loop over all fixed-step delta A operators ...
      for deltaAOperator in [o for o in self.getVar('templates') if isinstance(o, DeltaAOperator) and isinstance(o.integrator, FixedStep)]:
        # ... adding the noise vectors that are dependencies of that delta A operator
        noiseVectorsNeedingAlias.update([v for v in deltaAOperator.dependencies if isinstance(v, NoiseVector)])
        
      for noiseVector in noiseVectorsNeedingAlias:
        noiseVector.aliases.add('_%s2' % noiseVector.id)
    
