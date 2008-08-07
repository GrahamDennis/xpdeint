#!/usr/bin/env python
# encoding: utf-8
"""
_SICDeltaAOperator.py

Created by Graham Dennis on 2008-08-07.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Operators.DeltaAOperator import DeltaAOperator

from xpdeint.ParserException import ParserException

class _SICDeltaAOperator (DeltaAOperator):
  def __init__(self, *args, **KWs):
    DeltaAOperator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.crossPropagationDimension           = None
    self.crossPropagationDirection           = None
    self.boundaryConditionDependenciesEntity = None
    self.boundaryConditionCodeEntity         = None
    self.crossIntegrationVectors             = set()
    self.crossIntegrationVectorsEntity       = None
    self.crossPropagationCodeEntity          = None
    self.crossPropagationDependenciesEntity  = None
    
  
  @property
  def integrator(self):
    # Our parent is the operator container, and its parent is the integrator
    return self.parent.parent
  
  def bindNamedVectors(self):
    super(_SICDeltaAOperator, self).bindNamedVectors()
    
    if self.boundaryConditionDependenciesEntity:
      self.dependencies.update(self.vectorsFromEntity(self.boundaryConditionDependenciesEntity))
    
    if self.crossIntegrationVectorsEntity:
      self.crossIntegrationVectors.update(self.vectorsFromEntity(self.crossIntegrationVectorsEntity))
      if self.integrationVectors.intersection(self.crossIntegrationVectors):
        badVectors = self.integrationVectors.intersection(self.crossIntegrationVectors)
        raise ParserException(self.crossIntegrationVectorsEntity.xmlElement,
                              "Can't have a vector being integrated by both a cross-propagator and an integration block.\n"
                              "The vectors causing the problems are: %s" % ', '.join([v.name for v in badVectors]))
      self.dependencies.update(self.crossIntegrationVectors)
      
    if self.crossPropagationDependenciesEntity:
      self.dependencies.update(self.vectorsFromEntity(self.crossPropagationDependenciesEntity))
  
  
  def preflight(self):
    super(_SICDeltaAOperator, self).preflight()
    # Construct the operator components dictionary for the cross-propagation vectors
    for crossIntegrationVector in self.crossIntegrationVectors:
      for componentName in crossIntegrationVector.components:
        derivativeString = "d%s_d%s" % (componentName, self.crossPropagationDimension)
        
        # Map of operator names to vector -> component list dictionary
        self.operatorComponents[derivativeString] = {crossIntegrationVector: [componentName]}
    
    if self.crossPropagationDirection == '-':
      self.loopingOrder = _SICDeltaAOperator.LoopingOrder.StrictlyDecreasingOrder
    
