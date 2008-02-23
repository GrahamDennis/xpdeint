#!/usr/bin/env python
# encoding: utf-8
"""
_Operator.py

This contains all the pure-python code for Operator.tmpl

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from ScriptElement import ScriptElement
from ParserException import ParserException

class _Operator (ScriptElement):
  evaluateOperatorFunctionArgument = 'double _step'
  
  # Operator kinds
  IPOperatorKind     = 1
  OtherOperatorKind  = 2
  DeltaAOperatorKind = 3
  
  operatorKind = OtherOperatorKind
  
  vectorsMustBeInSubsetsOfIntegrationField = True
  
  calculateOperatorFieldFunctionArguments = ''
  
  def __init__(self, field, integrator, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.dependenciesEntity = None
    self.operatorComponents = {}
    self.operatorVector = None
    self.resultVector = None
    self.operatorNumber = -1
    self.integrator = integrator
    self.field = field
    self.operatorNumber = len(self.integrator.operators)
    integrator.operators.append(self)
    self._children = []
    self._loopingField = None
  
  # The children
  @property
  def children(self):
    # Return either or both of operatorVector and resultVector
    # depending on whether or not they are 'None'
    # And also return the _children
    result = filter(lambda x: x, [self.operatorVector, self.resultVector])
    result.extend(self._children)
    return result
  
  @property
  def name(self):
    return 'operator' + str(self.operatorNumber)
  
  @property
  def id(self):
    return ''.join([self.integrator.name, '_', self.name])
  
  @property
  def operatorTargetVectorsSet(self):
    setOfTargetVectors = set()
    
    # Loop over the vectors that the operators are going to operate on
    for operatorTargetVectors in self.operatorComponents.itervalues():
      setOfTargetVectors.update(set(operatorTargetVectors.keys()))
    
    return setOfTargetVectors
  
  
  @property
  def defaultOperatorSpace(self):
    return self.field.spaceMask
  
  def _getOperatorSpace(self):
    if not self.hasattr('_operatorSpace'):
      return self.defaultOperatorSpace
    else:
      return self._operatorSpace
  
  def _setOperatorSpace(self, newOperatorSpace):
    self._operatorSpace = newOperatorSpace
  
  operatorSpace = property(_getOperatorSpace, _setOperatorSpace)
  del _getOperatorSpace, _setOperatorSpace
  
  def _getLoopingField(self):
    return self._loopingField or self.field
  
  def _setLoopingField(self, value):
    self._loopingField = value
  
  loopingField = property(_getLoopingField, _setLoopingField)
  del _getLoopingField, _setLoopingField
  
  def bindNamedVectors(self):
    if self.dependenciesEntity:
      dependencies = self.vectorsFromEntity(self.dependenciesEntity)
      
      for dependency in dependencies:
        if not (dependency.initialSpace & self.field.spaceMask) == (self.operatorSpace & dependency.field.spaceMask):
          if not dependency.type == 'complex':
            raise ParserException(self.dependenciesEntity.xmlElement,
                    "Cannot satisfy dependence on vector '%s' because it is not "
                    "of type complex, and needs to be fourier transformed for this operator." % dependency.name)
          else:
            dependency.needsFourierTransforms = True
        
        if self.vectorsMustBeInSubsetsOfIntegrationField and not dependency.field.isSubsetOfField(self.field):
          raise ParserException(self.dependenciesEntity.xmlElement,
                  "Can't depend on a vector that is in a field that has dimensions that "
                  "aren't in this field (%s).\n"
                  "The vector causing this problem is '%s'." 
                  % (self.field.name, dependency.vector.name))
      
      self.dependencies.update(dependencies)
    
    if self.resultVector:
      self.resultVector.spacesNeeded.add(self.operatorSpace)
    super(_Operator, self).bindNamedVectors()
  
  
