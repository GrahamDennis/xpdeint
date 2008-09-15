#!/usr/bin/env python
# encoding: utf-8
"""
_ComputedVector.py

This contains all the pure-python code for ComputedVector.tmpl

Created by Graham Dennis on 2008-03-12.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Vectors.VectorElement import VectorElement
from xpdeint.Geometry.FieldElement import FieldElement

from xpdeint.Function import Function
from xpdeint.Utilities import lazyproperty

class _ComputedVector (VectorElement):
  isComputed = True
  
  def __init__(self, *args, **KWs):
    VectorElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.loopingField = None
    self.dependenciesEntity = None
    self._integratingComponents = True
    self._evaluationSpace = 0
    self.evaluationCodeEntity = None
    
    evaluateFunctionName = ''.join(['_', self.id, '_evaluate'])
    evaluateFunction = Function(name = evaluateFunctionName,
                               args = [],
                               implementation = self.evaluateFunctionContents)
    self.functions['evaluate'] = evaluateFunction
    
    
  
  @lazyproperty
  def noiseField(self):
    return self.loopingField
  
  def _getEvaluationSpace(self):
    return self._evaluationSpace
  
  def _setEvaluationSpace(self, value):
    self._evaluationSpace = value
    self.initialSpace = value & self.field.spaceMask
  
  evaluationSpace = property(_getEvaluationSpace, _setEvaluationSpace)
  del _getEvaluationSpace, _setEvaluationSpace
  
  def _getIntegratingComponents(self):
    return self._integratingComponents
  
  def _setIntegratingComponents(self, value):
    self._integratingComponents = value
    # The computed vector only needs initialisation to zero if we are integrating.
    self.needsInitialisation = value
  
  integratingComponents = property(_getIntegratingComponents, _setIntegratingComponents)
  del _getIntegratingComponents, _setIntegratingComponents
  
  def bindNamedVectors(self):
    super(VectorElement, self).bindNamedVectors()
    
    # This code must be here and not in preflight because _Stochastic needs to be able
    # to work out our noiseField, and that occurs in preflight. As we don't know what
    # order the templates' preflight functions will be called in, we have to put this in
    # bindNamedVectors to make sure that loopingField exists before the preflight stage.
    loopingDimensionNames = set([dim.name for dim in self.field.dimensions])
    for dependency in self.dependencies:
      loopingDimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    self.loopingField = FieldElement.sortedFieldWithDimensionNames(loopingDimensionNames)
  
  def preflight(self):
    super(VectorElement, self).preflight()
    
    if self.dependenciesEntity and self.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
      dependenciesXMLElement = self.dependenciesEntity.xmlElement
      self.evaluationSpace = self.loopingField.spaceFromString(dependenciesXMLElement.getAttribute('fourier_space'),
                                                               xmlElement = dependenciesXMLElement)
    
    # Our components are constructed by an integral if the looping field doesn't have the same
    # dimensions as the field to which the computed vector belongs.
    self.integratingComponents = not self.loopingField.isEquivalentToField(self.field)
  

