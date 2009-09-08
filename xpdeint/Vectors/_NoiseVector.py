#!/usr/bin/env python
# encoding: utf-8
"""
_NoiseVector.py

This contains all the pure-python code for NoiseVector.tmpl

Created by Joe Hope on 2009-08-17.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Vectors.VectorElement import VectorElement

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
    
  
  def initialiseSeeds(self):
    return self.randomVariable.generator.initialiseSeeds()
