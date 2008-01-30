#!/usr/bin/env python
# encoding: utf-8
"""
_StochasticFeature.py

Created by Graham Dennis on 2008-01-13.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from _Feature import _Feature
from VectorInitialisationCDATA import VectorInitialisationCDATA
from DeltaAOperator import DeltaAOperator

class _StochasticFeature (_Feature):
  def preflight(self):
    # We need to iterate over everything that could possibly need noises
    # The best way to do that is to have the ability to iterate over everything
    # and select those that have a 'canHaveNoises' attribute or the like.
    # Though, that does seem slightly backwards. No, we shouldn't do that
    # We should maintain a list here of things that can have noises.
    # This means we need to maintain a list of all instances of certain classes
    # 
    # We need to do this to determine which fields need noise vectors, and then
    # to construct these noise vectors
    #
    # Note that someone (maybe this class) needs to replace the named noises in
    # these classes (as read by the parser) with the actual noise objects
    
    classesThatCanUseNoises = set([VectorInitialisationCDATA, DeltaAOperator])
    objectsThatMightUseNoises = set()
    
    objectMap = self.getVar('objectMap')
    
    for c in classesThatCanUseNoises:
      objectsThatMightUseNoises.update(objectMap[c])
    
    
    
    super(_Feature, self).preflight()
  
