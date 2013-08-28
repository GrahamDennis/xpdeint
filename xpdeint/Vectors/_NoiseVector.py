#!/usr/bin/env python
# encoding: utf-8
"""
_NoiseVector.py

This contains all the pure-python code for NoiseVector.tmpl

Created by Joe Hope on 2009-08-17.

Copyright (c) 2009-2012, Joe Hope

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

from xpdeint.Vectors.VectorElement import VectorElement
from xpdeint.Geometry.NonUniformDimensionRepresentation import NonUniformDimensionRepresentation

from xpdeint.Function import Function

class _NoiseVector (VectorElement):
  isNoise = True
  
  def __init__(self, *args, **KWs):
    localKWs = self.extractLocalKWs(['staticNoise'], KWs)
    
    VectorElement.__init__(self, *args, **KWs)
    
    self.static = localKWs['staticNoise']
    
    args = []
    if not self.static:
      args.append(('real', '_step'))
    else:
      self.isComputed = True
    
    evaluateFunctionName = ''.join(['_', self.id, '_evaluate'])
    evaluateFunction = Function(
      name = evaluateFunctionName,
      args = args,
      implementation = self.evaluateFunctionContents
    )
    self.functions['evaluate'] = evaluateFunction
    
    if not self.static:
      splitFunctionName = ''.join(['_', self.id, '_split'])
      splitFunction = Function(
        name = splitFunctionName,
        args = [('real', '_new_step'), ('real', '_old_step'), (self.type + '*', '_old_array')],
        implementation = self.splitFunctionContents
      )
      self.functions['split'] = splitFunction
    
    self.basesNeeded.add(self.initialBasis)
    
    self.needsInitialisation = False
  
  @property
  def spatiallyIndependentVolumeElement(self):
    reps = self.field.inBasis(self.initialBasis)
    result = []
    for rep in reps:
      if isinstance(rep, NonUniformDimensionRepresentation):
        pass
      elif rep.type == 'long':
        pass # Integer step, so nothing interesting
      elif rep.type == 'real':
        result.append(rep.stepSize)
        result.append(rep.volumePrefactor)
      else:
        assert False, "Unknown dimension representation type %s" % rep.type
    if not result:
      return '1.0'
    return '(' + ' * '.join(result) + ')'
  
  @property
  def nonUniformDimReps(self):
    return [rep for rep in self.field.inBasis(self.initialBasis) if isinstance(rep, NonUniformDimensionRepresentation)]
  
  def initialiseGlobalSeeds(self):
    return self.randomVariable.generator.initialiseGlobalSeeds()
  
  def initialiseLocalSeeds(self):
    return self.randomVariable.generator.initialiseLocalSeeds()
