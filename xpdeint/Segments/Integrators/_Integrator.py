#!/usr/bin/env python
# encoding: utf-8
"""
_Integrator.py

This contains all the pure-python code for Integrator.tmpl

Created by Graham Dennis on 2007-10-18.

Copyright (c) 2007-2012, Graham Dennis

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

from xpdeint.Segments._Segment import _Segment

from xpdeint.Operators.NonConstantIPOperator import NonConstantIPOperator
from xpdeint.ParserException import ParserException
from xpdeint.Utilities import lazy_property, leastCommonMultiple
from xpdeint.Function import Function
from itertools import chain

class _Integrator (_Segment):
  
  canBeInitialisedEarly = True
  
  def __init__(self, stepperClass, *args, **KWs):
    _Segment.__init__(self, *args, **KWs)
    
    # Set default variables
    self.samplesEntity = None
    self.samples = []
    self._integrationVectors = set()
    self.homeBasis = None
    self.cutoff = 1e-3
    self.stepStartOperatorContainers = []
    self.intraStepOperatorContainers = []
    self.stepEndOperatorContainers = []
    self.localVectors = set()
    assert stepperClass
    self.stepper = stepperClass(parent = self, **self.argumentsToTemplateConstructors)
    self._children.append(self.stepper)
    
    functionNamePrefix = '_' + self.id
    
    self.functions['deltaA'] = Function(name = functionNamePrefix + '_calculate_delta_a',
                                        args = [('real', '_step')], 
                                        implementation = self.deltaAFunctionBody,
                                        returnType = 'inline void')
    
    self.functions['ipEvolve'] = Function(name = functionNamePrefix + '_ip_evolve',
                                          args = [('int', '_exponent')],
                                          implementation = self.ipEvolveFunctionBody,
                                          returnType = 'inline void')
    
    self.functions['nonconstantIPFields'] = Function(name = functionNamePrefix + '_calculate_nonconstant_ip_fields',
                                                     args = [('real', '_step'), ('int', '_exponent'), ('int', '_arrayIndex')],
                                                     implementation = self.nonconstantIPFieldsFunctionBody,
                                                     returnType = 'inline void')
    
  
  @property
  def children(self):
    children = super(_Integrator, self).children
    children.extend(chain(self.stepStartOperatorContainers, self.intraStepOperatorContainers, self.stepEndOperatorContainers, \
                          self.localVectors))
    return children
  
  @property
  def integrationVectors(self):
    if self._integrationVectors:
      return self._integrationVectors.copy()
    
    deltaAOperators = [oc.deltaAOperator for oc in self.intraStepOperatorContainers if oc.deltaAOperator]
    for op in deltaAOperators:
      self._integrationVectors.update(op.integrationVectors)
    
    return self._integrationVectors.copy()
  
  @lazy_property
  def dynamicNoiseVectors(self):
    """Returns the dynamic noise vectors required by the integrator."""
    
    return [vector for vector in self.evaluationOrderForVectors(
            self.dynamicVectorsNeedingPrecalculationForOperatorContainers(self.intraStepOperatorContainers), 
            static = False, predicate = lambda x: x.isComputed or x.isNoise) if vector.isNoise]

  @lazy_property
  def extraIntegrationArrayNames(self):
    return self.stepper.extraIntegrationArrayNames
  
  @lazy_property
  def ipPropagationStepFractions(self):
    return self.stepper.ipPropagationStepFractions
  
  @lazy_property
  def nonconstantIPFields(self):
    return self.stepper.nonconstantIPFields
  
  @lazy_property
  def stepCount(self):
    return leastCommonMultiple([sample for sample in self.samples])
  
  @property
  def integrationOrder(self):
    return self.stepper.integrationOrder
  
  @property
  def operatorContainers(self):
    return list(chain(self.stepStartOperatorContainers, self.intraStepOperatorContainers, self.stepEndOperatorContainers))
  
  @property
  def integrationFields(self):
    return set([v.field for v in self.integrationVectors])
  
  # List of the operator containers in descending order of the number of dimensions in their fields.
  #
  # This is needed because when delta A operators are evaluated, they replace the components
  # with their propagation-dimension increments. i.e. They do phi = dphi_dt * dt
  #
  # As a result, we need to be very particular about the order in which the delta A operators are evaluated.
  # We can't have a delta A operator for a vector before another delta A operator that might depend on that
  # vector.
  #
  # The solution used is to order the delta A operators in descending order of the
  # number of dimensions in its field, because while it would be sensible for a field with 3 dimensions to depend
  # on another field with 0 or 1 dimensions, it doesn't make sense for a 0 or 1 dimensional field to depend directly
  # on a 3 dimensional field. It may depend on the 3 dimensional field through moments of the field, however they will
  # be calculated in other operators that would have already been evaluated.
  def intraStepOperatorContainersInFieldDescendingOrder(self):
    operatorContainers = self.intraStepOperatorContainers[:]
    operatorContainers.sort(lambda x, y: cmp(len(x.field.dimensions), len(y.field.dimensions)), reverse=True)
    return operatorContainers
  
  def ipEvolveFunctionBody(self, function):
    return '\n'.join([oc.evaluateIPOperators(parentFunction = function) for oc in self.operatorContainers])
  
  def nonconstantIPFieldsFunctionBody(self, function):
    result = []
    for oc in self.operatorContainers:
      nonconstantIPOperators = [op for op in oc.ipOperators if isinstance(op, NonConstantIPOperator)]
      if nonconstantIPOperators:
        result.append(oc.callOperatorFunctionWithArguments('calculateOperatorField', nonconstantIPOperators, parentFunction=function))
    
    return '\n'.join(result)
  
  def bindNamedVectors(self):
    super(_Integrator, self).bindNamedVectors()
    
    momentGroups = self.getVar('momentGroups')
    
    if not self.samplesEntity:
      self.samples = [0] * len(momentGroups)
    else:
      samplesList = self.samplesEntity.value
      samplesElement = self.samplesEntity.xmlElement
      
      if not len(samplesList) == len(momentGroups):
        raise ParserException(samplesElement, "The number of entries (%i) does not match the "
                                              "number of moment groups (%i)." % \
                                              (len(samplesList), len(momentGroups)))
      
      self.samples = [int(sampleCountString) for sampleCountString in samplesList]
      
      for momentGroup, sampleCount in zip(momentGroups, self.samples):
        if sampleCount and not (self.stepCount % sampleCount) == 0:
          raise ParserException(samplesElement, "Sample count does not evenly divide the number of steps")
        
        momentGroup.addSamplePoints(sampleCount * self.totalCycles)
    
    
  def preflight(self):
    super(_Integrator, self).preflight()
    
    self.registerVectorsRequiredInBasis(self.integrationVectors, self.homeBasis)
  
