#!/usr/bin/env python
# encoding: utf-8
"""
_Integrator.py

This contains all the pure-python code for Integrator.tmpl

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Segments._Segment import _Segment

from xpdeint.Operators.NonConstantIPOperator import NonConstantIPOperator
from xpdeint.ParserException import ParserException
from xpdeint.Function import Function

class _Integrator (_Segment):
  
  canBeInitialisedEarly = True
  
  def __init__(self, *args, **KWs):
    _Segment.__init__(self, *args, **KWs)
    
    # Set default variables
    self.samplesEntity = None
    self.samples = []
    self._integrationVectors = set()
    self.homeSpace = 0
    self.cutoff = 1e-3
    self.stepStartOperatorContainers = []
    self.intraStepOperatorContainers = []
    self.stepEndOperatorContainers = []
    self.computedVectors = set()
    self._children = []
    
    functionNamePrefix = '_' + self.id
    
    self.functions['deltaA'] = Function(name = functionNamePrefix + '_calculate_delta_a',
                                        args = [('double', '_step')], 
                                        implementation = self.deltaAFunctionBody,
                                        returnType = 'inline void')
    
    self.functions['ipEvolve'] = Function(name = functionNamePrefix + '_ip_evolve',
                                          args = [('int', '_exponent')],
                                          implementation = self.ipEvolveFunctionBody,
                                          returnType = 'inline void')
    
    self.functions['nonconstantIPFields'] = Function(name = functionNamePrefix + '_calculate_nonconstant_ip_fields',
                                                     args = [('double', '_step'), ('int', '_exponent'), ('int', '_arrayIndex')],
                                                     implementation = self.nonconstantIPFieldsFunctionBody,
                                                     returnType = 'inline void')
    
  
  @property
  def children(self):
    result = []
    for array in [self.stepStartOperatorContainers, self.intraStepOperatorContainers, self.stepEndOperatorContainers, self.computedVectors, self._children]:
      result.extend(array)
    return result
  
  @property
  def integrationVectors(self):
    if self._integrationVectors:
      return self._integrationVectors.copy()
    
    deltaAOperators = [oc.deltaAOperator for oc in self.intraStepOperatorContainers if oc.deltaAOperator]
    for op in deltaAOperators:
      self._integrationVectors.update(op.integrationVectors)
    
    return self._integrationVectors.copy()
  
  @property
  def operatorContainers(self):
    result = []
    for array in [self.stepStartOperatorContainers, self.intraStepOperatorContainers, self.stepEndOperatorContainers]:
      result.extend(array)
    return result
  
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
  
  def preflight(self):
    super(_Integrator, self).preflight()
    
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
      
      for momentGroup, sampleCountString in zip(momentGroups, samplesList):
        sampleCount = int(sampleCountString)
        if sampleCount and not (self.stepCount % sampleCount) == 0:
          raise ParserException(samplesElement, "Sample count does not evenly divide the number of steps")
        self.samples.append(sampleCount)
        
        momentGroup.outputField.dimensionWithName(self.propagationDimension).inSpace(0).lattice += sampleCount * self.totalCycles
      
  
