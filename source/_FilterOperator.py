#!/usr/bin/env python
# encoding: utf-8
"""
_FilterOperator.py

Created by Graham Dennis on 2008-01-01.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from NonConstantOperator import NonConstantOperator
from ParserException import ParserException

class _FilterOperator (NonConstantOperator):
  operatorKind = NonConstantOperator.OtherOperatorKind
  vectorsMustBeInSubsetsOfIntegrationField = False
  
  def __init__(self, *args, **KWs):
    NonConstantOperator.__init__(self, *args, **KWs)
    
    # Set default variables
    self.integratingMoments = True
  
  @property
  def defaultOperatorSpace(self):
    return 0

  
  def bindNamedVectors(self):
    if self.dependenciesEntity:
      dependencies = self.vectorsFromEntity(self.dependenciesEntity)
      for dependency in dependencies:
        if not dependency.field.isSubsetOfField(self.sourceField):
          vectorName = dependency.name
          raise ParserException(self.dependenciesEntity.xmlElement,
                  "Filter vectors must belong to fields which only contain dimensions that "
                  "exist in the source field.\n"
                  "Vector '%(vectorName)s' caused this problem." % locals())
        
      self.dependencies.update(dependencies)
    
    super(_FilterOperator, self).bindNamedVectors()
  

