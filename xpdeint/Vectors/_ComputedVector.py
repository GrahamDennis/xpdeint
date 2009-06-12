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
from xpdeint.Utilities import lazy_property

class _ComputedVector (VectorElement):
  isComputed = True
  
  def __init__(self, *args, **KWs):
    VectorElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self._integratingComponents = True
    
    evaluateFunctionName = ''.join(['_', self.id, '_evaluate'])
    evaluateFunction = Function(name = evaluateFunctionName,
                               args = [],
                               implementation = self.evaluateFunctionContents)
    self.functions['evaluate'] = evaluateFunction
  
  @lazy_property
  def noiseField(self):
    return self.codeBlocks['evaluation'].field
  
  @property
  def dependencies(self):
    return self.codeBlocks['evaluation'].dependencies
  
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
    
    evaluationCodeBlock = self.codeBlocks['evaluation']
    # This code to determine the evaluation looping field used to be in bindNamedVectors because
    # _Stochastic needed access to 'noiseField' during its preflight. However, the way that the
    # Stochastic feature works at the moment is silly, and is causing design problems. The better
    # design is to use noise vectors but until that is implemented, the Stochastic feature will
    # be dealt with specially.
    loopingDimensionNames = set([dim.name for dim in self.field.dimensions])
    for dependency in evaluationCodeBlock.dependencies:
      loopingDimensionNames.update([dim.name for dim in dependency.field.dimensions])
    
    evaluationCodeBlock.field = FieldElement.sortedFieldWithDimensionNames(loopingDimensionNames)
    
  def preflight(self):
    super(_ComputedVector, self).preflight()
    
    evaluationCodeBlock = self.codeBlocks['evaluation']
    if evaluationCodeBlock.dependenciesEntity and evaluationCodeBlock.dependenciesEntity.xmlElement.hasAttribute('fourier_space'):
      dependenciesXMLElement = evaluationCodeBlock.dependenciesEntity.xmlElement
      evaluationSpace = evaluationCodeBlock.field.spaceFromString(dependenciesXMLElement.getAttribute('fourier_space'),
                                                                  xmlElement = dependenciesXMLElement)
      evaluationCodeBlock.space = evaluationSpace
    # Set the space so that it is known that this vector is required in the evaluation space.
    self.initialSpace = evaluationCodeBlock.space
    
    # Our components are constructed by an integral if the looping field doesn't have the same
    # dimensions as the field to which the computed vector belongs.
    self.integratingComponents = not evaluationCodeBlock.field.isEquivalentToField(self.field)
  

