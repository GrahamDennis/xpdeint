#!/usr/bin/env python
# encoding: utf-8
"""
_DeltaAOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""


from Operator import Operator
from ParserException import ParserException

class _DeltaAOperator (Operator):
  operatorKind = Operator.DeltaAOperatorKind
  def __init__(self, *args, **KWs):
    Operator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.integrationVectorsEntity = None
    self.integrationVectors = set()
  
  @property
  def defaultOperatorSpace(self):
    return 0
  
  def bindNamedVectors(self):
    if self.integrationVectorsEntity:
      self.integrationVectors = self.vectorsFromEntity(self.integrationVectorsEntity)
      
      for integrationVector in self.integrationVectors:
        if not integrationVector.field == self.field:
          raise ParserException(self.integrationVectorsEntity.xmlElement, 
                                "Cannot integrate vector '%s' in this operators element as it "
                                "belongs to a different field" % integrationVector.name)
        
        for componentName in integrationVector.components:
          derivativeString = "d%s_d%s" % (componentName, self.getVar('propagationDimension'))
          
          # Map of operator names to vector -> component list dictionary
          self.operatorComponents[derivativeString] = {integrationVector: [componentName]}
          
      self.integrator.vectors.update(self.integrationVectors)
      self.dependencies.update(self.integrationVectors)
    
    super(_DeltaAOperator, self).bindNamedVectors()
    
  

