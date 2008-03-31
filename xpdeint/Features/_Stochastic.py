#!/usr/bin/env python
# encoding: utf-8
"""
_Stochastic.py

Created by Graham Dennis on 2008-01-13.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature
from xpdeint.Vectors.VectorElement import VectorElement
from xpdeint.Vectors.ComputedVector import ComputedVector
from xpdeint.Vectors.VectorInitialisationFromCDATA import VectorInitialisationFromCDATA
from xpdeint.Vectors.VectorInitialisationFromXSIL import VectorInitialisationFromXSIL
from xpdeint.Operators.DeltaAOperator import DeltaAOperator
from xpdeint.Segments.Integrators.FixedStep import FixedStep as FixedStepIntegrator
from xpdeint.Segments.Integrators.AdaptiveStep import AdaptiveStep as AdaptiveStepIntegrator

from xpdeint.ParserException import ParserException

class _Stochastic (_Feature):
  @property
  def children(self):
    return self.noises
  
  def noisesAndFieldsForIntegrator(self, integrator):
    result = []
    
    for field in integrator.integrationFields:
      deltaAOperatorList = [oc.deltaAOperator for oc in integrator.operatorContainers if oc.field == field]
      assert len(deltaAOperatorList) == 1
      deltaAOperator = deltaAOperatorList[0]
      
      noisesNeeded = self.noises[:]
      if deltaAOperator.hasattr('noises'):
        noisesNeeded = deltaAOperator.noises[:]
      
      result.extend([(noise, field) for noise in noisesNeeded])
    
    return result
  
  def xsilOutputInfo(self, dict):
    return self.implementationsForChildren('xsilOutputInfo', dict)
  
  def preflight(self):
    super(_Feature, self).preflight()
    
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
    
    classesThatCanUseNoises = (VectorInitialisationFromCDATA, VectorInitialisationFromXSIL, ComputedVector, DeltaAOperator)
    
    objectsThatMightUseNoises = [o for o in self.getVar('templates') if isinstance(o, classesThatCanUseNoises)]
    
    noiseNameMap = dict([(noise.prefix, noise) for noise in self.noises])
    fieldToNoisesMap = dict()
    
    for o in objectsThatMightUseNoises:
      noises = self.noises
      if o.hasattr('noisesEntity'):
        noises = []
        for noiseName in o.noisesEntity.value:
          if not noiseName in noiseNameMap:
            raise ParserException(o.noisesEntity.xmlElement, "Unknown noise prefix '%(noiseName)s'." % locals())
          noises.append(noiseNameMap[noiseName])
      
      o.noises = noises
      
      noiseField = None
      if o.hasattr('noiseField'):
        noiseField = o.noiseField
      else:
        noiseField = o.field
      
      if not noiseField in fieldToNoisesMap:
        fieldToNoisesMap[noiseField] = set()
      fieldToNoisesMap[noiseField].update(o.noises)
    
    for field, noises in fieldToNoisesMap.iteritems():
      for noise in noises:
        if not noise.hasattr('noiseVectors'):
          noise.noiseVectors = dict()
        
        noiseVector = VectorElement(name = '%s_noises' % noise.prefix, field = field,
                                    transformFree = True, # This attribute says that this vector is always in the right field.
                                    **self.argumentsToTemplateConstructors)
        noiseVector.type = 'double'
        noiseVector.needsInitialisation = False
        noiseVector.components = ['%s_%i' % (noise.prefix, i) for i in range(1, noise.noiseCount + 1)]
        field.managedVectors.add(noiseVector)
        
        noise.noiseVectors[field] = noiseVector
    
    for o in objectsThatMightUseNoises:
      # Add to the dependencies for this object the noise vectors corresponding to the noises
      # that this object wants to use
      o.dependencies.update([noise.noiseVectorForField(noiseField) for noise in o.noises])
    
    
    # For each adaptive step integrator, we need to make sure that the noises being used are
    # either gaussian or poissonian
    for deltaAOperator in [o for o in objectsThatMightUseNoises if isinstance(o, DeltaAOperator) and isinstance(o.integrator, AdaptiveStepIntegrator)]:
      for noise in deltaAOperator.noises:
        if noise.noiseDistribution not in ('gaussian', 'poissonian'):
          raise ParserException(self.xmlElement, "Can't use a noise with a '%s' distribution in an adaptive integrator. "
                                                 "Only gaussian or poissonian noises can be used." % noise.noiseDistribution)
    
    # For each adaptive step integrator using noises, we need to reduce the order of the integrator
    integratorsUsingNoises = set([o.integrator for o in objectsThatMightUseNoises if isinstance(o, DeltaAOperator) and isinstance(o.integrator, AdaptiveStepIntegrator)])
    for integrator in integratorsUsingNoises:
      integrator.successfulStepExponent *= 2.0
      integrator.unsuccessfulStepExponent *= 2.0
    
    # When we have error checking, every noise vector used by a delta a operator in a fixed step integrator
    # needs a '2' noise vector alias for generating two half-step noises and adding them.
    self.noiseAliases = []
    if 'ErrorCheck' in self.getVar('features'):
      noiseVectorsNeedingAlias = set()
      # Loop over all fixed-step delta A operators ...
      for deltaAOperator in [o for o in objectsThatMightUseNoises if isinstance(o, DeltaAOperator) and isinstance(o.integrator, FixedStepIntegrator)]:
        # ... adding the noise vectors used by those noises to the set of noise vectors needing aliases
        noiseVectorsNeedingAlias.update([noise.noiseVectorForField(deltaAOperator.field) for noise in deltaAOperator.noises])
      
      for noiseVector in noiseVectorsNeedingAlias:
        noiseVector.aliases.add('_%s2' % noiseVector.id)
        self.noiseAliases.append(noiseVector)
    
    
  
