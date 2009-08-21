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
    VectorElement.__init__(self, *args, **KWs)
    
    evaluateFunctionName = ''.join(['_', self.id, '_evaluate'])
    evaluateFunction = Function(name = evaluateFunctionName,
                               args = [('double','_step')],
                               implementation = self.evaluateFunctionContents)
    self.functions['evaluate'] = evaluateFunction
    self.basesNeeded.add(self.initialBasis)
    
    self.needsInitialisation = False
