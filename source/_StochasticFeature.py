#!/usr/bin/env python
# encoding: utf-8
"""
_StochasticFeature.py

Created by Graham Dennis on 2008-01-13.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from _Feature import _Feature
from VectorElement import VectorElement
from VectorInitialisationCDATA import VectorInitialisationCDATA
from DeltaAOperator import DeltaAOperator

from ParserException import ParserException

class _StochasticFeature (_Feature):
  
  @property
  def children(self):
    return self.noises
  
  def noisesAndFieldsForIntegrator(self, integrator):
    result = []
    
    for field in integrator.integrationFields:
      deltaAOperatorList = filter(lambda x: x.field == field and isinstance(x, DeltaAOperator), integrator.operators)
      assert len(deltaAOperatorList) == 1
      deltaAOperator = deltaAOperatorList[0]
      
      noisesNeeded = self.noises[:]
      if hasattr(deltaAOperator, 'noises'):
        noisesNeeded = deltaAOperator.noises[:]
      
      result.extend([(noise, field) for noise in noisesNeeded])
    
    return result
  
  def xsilOutputInfo(self, dict):
    return self.implementationsForClassesAndChildren('xsilOutputInfo', dict)
  
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
    
    objectsThatMightUseNoises = [o for o in self.getVar('templates') if isinstance(o, (VectorInitialisationCDATA, DeltaAOperator))]
    
    noiseNameMap = dict([(noise.prefix, noise) for noise in self.noises])
    fieldToNoisesMap = dict()
    
    for o in objectsThatMightUseNoises:
      noises = self.noises
      if hasattr(o, 'noisesEntity'):
        noises = []
        for noiseName in o.noisesEntity.value:
          if not noiseName in noiseNameMap:
            raise ParserException(o.noisesEntity.xmlElement, "Unknown noise prefix '%(noiseName)s'." % locals())
          noises.append(noiseNameMap[noiseName])
      
      o.noises = noises
      if not o.field in fieldToNoisesMap:
        fieldToNoisesMap[o.field] = set()
      fieldToNoisesMap[o.field].update(o.noises)
    
    for field, noises in fieldToNoisesMap.iteritems():
      for noise in noises:
        if not hasattr(noise, 'noiseVectors'):
          noise.noiseVectors = dict()
        
        noiseVector = VectorElement(name = '%s_noises' % noise.prefix, field = field,
                                    searchList = self.searchListTemplateArgument,
                                    filter = self.filterTemplateArgument)
        noiseVector.type = 'double'
        noiseVector.needsInitialisation = False
        noiseVector.components = ['%s_%i' % (noise.prefix, i) for i in range(1, noise.noiseCount + 1)]
        field.managedVectors.add(noiseVector)
        
        noise.noiseVectors[field] = noiseVector
    
    for o in objectsThatMightUseNoises:
      # Add to the dependencies for this object the noise vectors corresponding to the noises
      # that this object wants to use
      o.dependencies.update([noise.noiseVectorForField(o.field) for noise in o.noises])
    
    
    integratorsUsingNoises = set([(o.integrator, o) for o in objectsThatMightUseNoises if isinstance(o, DeltaAOperator)])
    for integrator, deltaAOperator in integratorsUsingNoises:
      if hasattr(integrator, 'successfulStepExponent') and hasattr(integrator, 'unsuccessfulStepExponent'):
        for noise in deltaAOperator.noises:
          if noise.noiseDistribution not in ('gaussian', 'poissonian'):
            raise ParserException(self.xmlElement, "Only gaussian or poissonian noises can be used in adaptive integrators.")
        integrator.successfulStepExponent *= 2.0
        integrator.unsuccessfulStepExponent *= 2.0
    
    super(_Feature, self).preflight()
  
