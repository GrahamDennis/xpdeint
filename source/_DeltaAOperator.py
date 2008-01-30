#!/usr/bin/env python
# encoding: utf-8
"""
_DeltaAOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""


from NonConstantOperator import NonConstantOperator
from ParserException import ParserException

class _DeltaAOperator (NonConstantOperator):
  operatorKind = NonConstantOperator.DeltaAOperatorKind
  def __init__(self, *args, **KWs):
    NonConstantOperator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.integrationVectorsEntity = None
    self.integrationVectors = set()
  
  @property
  def defaultOperatorSpace(self):
    return 0
  
  def preflight(self):
    if self.integrationVectorsEntity:
      integrationVectors = self.vectorsFromEntity(self.integrationVectorsEntity)
      
      for integrationVector in integrationVectors:
        if not integrationVector.field == self.field:
          raise ParserException(self.integrationVectorsEntity.xmlElement, 
                                "Cannot integrate vector '%s' in this operators element as it "
                                "belongs to a different field" % integrationVector.name)
        
        for componentName in integrationVector.components:
          derivativeString = "d%s_d%s" % (componentName, self.getVar('propagationDimension'))
          
          # Map of operator names to vector -> component list dictionary
          self.operatorComponents[derivativeString] = {integrationVector: [componentName]}
          
      self.integrator.vectors.update(integrationVectors)
      self.dependencies.update(integrationVectors)
    
    super(_DeltaAOperator, self).preflight()
    
  

