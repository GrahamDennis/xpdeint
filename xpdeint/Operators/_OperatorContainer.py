#!/usr/bin/env python
# encoding: utf-8
"""
_OperatorContainer.py

Created by Graham Dennis on 2008-03-09.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

from xpdeint.Operators._Operator import _Operator
from xpdeint.ParserException import ParserException

class _OperatorContainer(ScriptElement):
  def __init__(self, *args, **KWs):
    legalKWs = ['field', 'name', 'sharedCodeKeyPath', 'dependenciesKeyPath', 'sharedCodeSpaceKeyPath']
    localKWs = {}
    for key in KWs.copy():
      if key in legalKWs:
        localKWs[key] = KWs[key]
        del KWs[key]
    
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default state
    self.ipOperators = []
    self.preDeltaAOperators = []
    self.deltaAOperator = None
    self.postDeltaAOperators = []
    self.field = localKWs.get('field', None)
    self._name = localKWs.get('name', None)
    
    # These key paths are the 'paths' to the actual attributes for our
    # 'sharedCode', 'dependencies' and 'sharedCodeSpace' proxy properties
    self.sharedCodeKeyPath = localKWs.get('sharedCodeKeyPath', 'deltaAOperator.propagationCodeEntity.value')
    self.dependenciesKeyPath = localKWs.get('dependenciesKeyPath', 'deltaAOperator.dependencies')
    self.sharedCodeSpaceKeyPath = localKWs.get('sharedCodeSpaceKeyPath', 'deltaAOperator.operatorSpace')
  
  def _getSharedCode(self):
    return self.valueForKeyPath(self.sharedCodeKeyPath)
  
  def _setSharedCode(self, value):
    return self.setValueForKeyPath(value, self.sharedCodeKeyPath)
  
  sharedCode = property(_getSharedCode, _setSharedCode)
  del _getSharedCode, _setSharedCode
  
  @property
  def dependencies(self):
    return self.valueForKeyPath(self.dependenciesKeyPath)
  
  @property
  def sharedCodeSpace(self):
    return self.valueForKeyPath(self.sharedCodeSpaceKeyPath)
  
  @property
  def name(self):
    if self._name:
      return self._name
    if not self.field:
      # We are deliberately not setting self._name here
      return ''
    self._name = 'container' + str(self.parent.operatorContainers.index(self))
    return self._name
  
  @property
  def operators(self):
    result = self.ipOperators[:]
    result.extend(self.preDeltaAOperators)
    if self.deltaAOperator:
      result.append(self.deltaAOperator)
    result.extend(self.postDeltaAOperators)
    return result
  
  @property
  def children(self):
    return self.operators
  
  @property
  def computedVectorsNeedingPrecalculation(self):
    result = set()
    for operator in self.operators:
      result.update(operator.computedVectorsNeedingPrecalculation)
    return result
  
  def addOperator(self, op):
    if op.operatorKind == _Operator.IPOperatorKind:
      self.ipOperators.append(op)
    elif op.operatorKind == _Operator.DeltaAOperatorKind:
      if self.deltaAOperator:
        raise ParserException(op.xmlElement, "For some reason we are trying to add two delta a operators to this operator container.")
      self.deltaAOperator = op
    elif not self.deltaAOperator:
      self.preDeltaAOperators.append(op)
    else:
      self.postDeltaAOperators.append(op)
    
    op.operatorNumber = len(self.operators) - 1
  
  
  def evaluateIPOperators(self, arguments = None):
    arguments = arguments or {}
    return self._evaluateOperatorsWithArgument(self.ipOperators, arguments)
  
  def evaluatePreDeltaAOperators(self, arguments = None):
    arguments = arguments or {}
    return self._evaluateOperatorsWithArgument(self.preDeltaAOperators, arguments)
  
  def evaluatePostDeltaAOperators(self, arguments = None):
    arguments = arguments or {}
    return self._evaluateOperatorsWithArgument(self.postDeltaAOperators, arguments)
  
  def evaluateDeltaAOperator(self, arguments = None):
    arguments = arguments or {}
    if self.deltaAOperator:
      return self._evaluateOperatorsWithArgument([self.deltaAOperator], arguments)
    else:
      return ''
  
  def evaluateOperators(self, arguments = None):
    arguments = arguments or {}
    assert not self.postDeltaAOperators and not self.deltaAOperator and not self.ipOperators
    return self._evaluateOperatorsWithArgument(self.preDeltaAOperators, arguments)
  
  def initialise(self):
    return '\n'.join([op.initialise() for op in self.operators])
  
  def finalise(self):
    return '\n'.join([op.finalise() for op in self.operators])
  
  
  def preflight(self):
    super(_OperatorContainer, self).preflight()
    
    if self.field and self.deltaAOperator:
      assert self.field == self.deltaAOperator.field
    

