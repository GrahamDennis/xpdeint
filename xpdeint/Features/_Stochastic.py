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
from xpdeint.Vectors.NoiseVector import NoiseVector
from xpdeint.Vectors.VectorInitialisationFromCDATA import VectorInitialisationFromCDATA
from xpdeint.Vectors.VectorInitialisationFromXSIL import VectorInitialisationFromXSIL
from xpdeint.Vectors.VectorInitialisationFromHDF5 import VectorInitialisationFromHDF5
from xpdeint.Operators.FilterOperator import FilterOperator
from xpdeint.Operators.DeltaAOperator import DeltaAOperator
from xpdeint.Segments.Integrators.FixedStep import FixedStep as FixedStepIntegrator
from xpdeint.Segments.Integrators.AdaptiveStep import AdaptiveStep as AdaptiveStepIntegrator

from xpdeint.ParserException import ParserException, parserWarning

class _Stochastic (_Feature):
  def __init__(self, *args, **KWs):
    _Feature.__init__(self, *args, **KWs)
    
    self.noises = []
  
  @property
  def children(self):
    children = super(_Stochastic, self).children
    children.extend(self.noises)
    return children
  
  def integratorNeedsNoises(self, integrator):
    for deltaAOperator in [oc.deltaAOperator for oc in integrator.operatorContainers if oc.deltaAOperator]:
      if deltaAOperator.hasattr('noises'):
        if deltaAOperator.noises:
          return True
      elif self.noises:
        return True
    
    return False
  
  def noisesForFieldInIntegrator(self, field, integrator):
    assert field in integrator.integrationFields
    
    deltaAOperatorList = [oc.deltaAOperator for oc in integrator.operatorContainers if oc.field == field and oc.deltaAOperator.noises]
    assert len(deltaAOperatorList) <= 1
    
    if not deltaAOperatorList: return []
    deltaAOperator = deltaAOperatorList[0]
    
    noisesNeeded = self.noises[:]
    if deltaAOperator.hasattr('noises'):
      noisesNeeded = deltaAOperator.noises[:]
    
    return noisesNeeded
  
  def adaptiveIntegratorsWithNoises(self):

    adaptiveIntegratorList = [ai for ai in self.getVar('templates') if isinstance(ai, AdaptiveStepIntegrator) and (ai.dynamicNoiseVectors or self.integratorNeedsNoises(ai))]

    return adaptiveIntegratorList

  def deltaAOperatorBasisForFieldInIntegrator(self, field, integrator):
    assert field in integrator.integrationFields
    
    deltaAOperatorList = [oc.deltaAOperator for oc in integrator.operatorContainers if oc.field == field and oc.deltaAOperator.noises]
    assert len(deltaAOperatorList) <= 1
    
    if not deltaAOperatorList: return None
    deltaAOperator = deltaAOperatorList[0]
    
    return deltaAOperator.operatorBasis
  
  def xsilOutputInfo(self, dict):
    return self.implementationsForChildren('xsilOutputInfo', dict)
  
  def preflight(self):
    super(_Stochastic, self).preflight()
    
    self.noiseVectors = [o for o in self.getVar('templates') if isinstance(o, NoiseVector)]
    
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
    
    classesThatCanUseNoises = (VectorInitialisationFromCDATA, VectorInitialisationFromXSIL, VectorInitialisationFromHDF5, ComputedVector, FilterOperator, DeltaAOperator)
    
    objectsThatMightUseNoises = [o for o in self.getVar('templates') if isinstance(o, classesThatCanUseNoises)]
    
    noiseNameMap = dict([(noise.prefix, noise) for noise in self.noises])
    fieldToNoisesMap = dict()
    
    for o in objectsThatMightUseNoises[:]:
      noises = self.noises
      if o.hasattr('noisesEntity'):
        noises = []
        for noiseName in o.noisesEntity.value:
          if not noiseName in noiseNameMap:
            raise ParserException(o.noisesEntity.xmlElement, "Unknown noise prefix '%(noiseName)s'." % locals())
          noises.append(noiseNameMap[noiseName])
      
      o.noises = noises
      
      if not o.noises:
        objectsThatMightUseNoises.remove(o)
        continue
      
      # The field in which the noises need to be evaluated will be the object's 'noiseField'
      # attribute if it exists, otherwise, we'll use the 'field' attribute.
      
      # The noiseField attribute is needed by ComputedVectors because they may exist in one field
      # but may be constructed from a larger field and so need the noise in that larger field.
      noiseField = o.noiseField
      assert noiseField
      
      if not noiseField in fieldToNoisesMap:
        fieldToNoisesMap[noiseField] = set()
      fieldToNoisesMap[noiseField].update(o.noises)
    
    for field, noises in fieldToNoisesMap.iteritems():
      for noise in noises:
        if not noise.hasattr('noiseVectors'):
          noise.noiseVectors = dict()
        
        noiseVector = VectorElement(name = '%s_noises' % noise.prefix, field = field,
                                    transformFree = True, # This attribute says that this vector is always in the right field.
                                    type = 'real',
                                    **self.argumentsToTemplateConstructors)
        noiseVector.needsInitialisation = False
        noiseVector.components = ['%s_%i' % (noise.prefix, i) for i in range(1, noise.noiseCount + 1)]
        field.managedVectors.add(noiseVector)
        
        noise.noiseVectors[field] = noiseVector
    
    for o in objectsThatMightUseNoises:
      # Add to the dependencies for this object the noise vectors corresponding to the noises
      # that this object wants to use
      noiseVectors = [noise.noiseVectorForField(o.noiseField) for noise in o.noises]
      o.dependencies.update(noiseVectors)
      # FIXME: Dodgy hack. Fortunately, this won't be needed once noise vectors are implemented.
      for codeBlock in o.codeBlocks.itervalues(): codeBlock.dependencies.update(noiseVectors)
    
    # For each adaptive step integrator, we need to make sure that the noises being used are
    # either gaussian or poissonian
    for deltaAOperator in [o for o in objectsThatMightUseNoises if isinstance(o, DeltaAOperator) and isinstance(o.integrator, AdaptiveStepIntegrator)]:
      # Give the user a warning to note that the adaptive integrators with stochastics is not guaranteed to converge to the correct solution.
      parserWarning(self.xmlElement, "The adaptive integrator with stochastics will not converge to the correct solution unless the "
                                     "timestep is limited by the non-stochastic elements of the equations.  The RK algorithms are accurate only "
                                     "if the solution to the SDE can be written as a Taylor series in the propagation dimension (time) and the noises. "
                                     "If this is the case, then there is probably an analytic solution to the SDE.\n"
                                     "You have been warned.")
      for noise in deltaAOperator.noises:
        if noise.noiseDistribution not in ('gaussian', 'poissonian'):
          raise ParserException(self.xmlElement, "Can't use a noise with a '%s' distribution in an adaptive integrator. "
                                                 "Only gaussian or poissonian noises can be used." % noise.noiseDistribution)
    
    # For each adaptive step integrator using noises, we need to reduce the order of the integrator
    adaptiveIntegratorsUsingNoises = set([o.integrator for o in objectsThatMightUseNoises
                                              if isinstance(o, DeltaAOperator) and isinstance(o.integrator, AdaptiveStepIntegrator)])
    for integrator in adaptiveIntegratorsUsingNoises:
      integrator.stepper.integrationOrder /= 2.0
    
    fixedStepIntegratorsUsingNoises = set([o.integrator for o in objectsThatMightUseNoises
                                              if isinstance(o, DeltaAOperator) and isinstance(o.integrator, FixedStepIntegrator)])
    if fixedStepIntegratorsUsingNoises:
      for computedVector in [o for o in objectsThatMightUseNoises if isinstance(o, ComputedVector)]:
        raise ParserException(
          self.xmlElement,
          "You have both computed vectors and a fixed step integrator that are both using noises. This is not safe. "
          "You should probably add the attribute noises=\"\" to the evaluation element of any computed vectors that don't need noises."
        )
    
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
    
  
