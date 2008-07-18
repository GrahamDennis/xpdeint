#!/usr/bin/env python
# encoding: utf-8
"""
OperatorContainer.py

Created by Graham Dennis on 2008-03-09.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement

from xpdeint.Operators._Operator import _Operator
from xpdeint.ParserException import ParserException

class OperatorContainer(ScriptElement):
  """
  The `OperatorContainer` is, as the name suggests, a container for operators.
  The idea is that there are many places where you want to be able to have a set
  of operators and you want to be execute all of them without worrying too much
  about what operators they are. 
  
  Similarly, some operators depend on a common (or 'shared') code block to determine
  their behaviour (e.g. IP and EX). The `OperatorContainer` abstracts exactly where
  this shared code block is and what its dependencies are so the operators don't need
  to know whether they are being used in an integrator or in moment group sampling,
  all they care about is that the `OperatorContainer` has been configured correctly.
  
  Configuring an OperatorContainer amounts to setting the `sharedCodeKeyPath`, 
  `dependenciesKeyPath` and `sharedCodeSpaceKeyPath` variables in the initialiser
  for `OperatorContainer`. `sharedCodeKeyPath` is a string that is a dotted-name
  lookup specifier for the string that is the 'shared' code block for this operator
  container. For example, in the case of an integrator, the 'shared' code block is the
  integration code ``'dphi_dt = L[phi] + V*phi; // etc.'`` In an integrator, this
  shared code belongs to the delta-a operator of the operator container. The 
  `sharedCodeSpaceKeyPath` is simply the space in which the 'shared' code block is
  evaluated, and `dependenciesKeyPath` is the key path to the dependencies that will
  be available when the shared code is evaluated. These three variables configure
  the three proxy variables on the `OperatorContainer`, `sharedCode`,
  `dependencies` and `sharedCodeSpace`. Proxies are used to refer to the actual variables
  instead of accessing them directly to enable write access to, for example, the shared code
  object (as is needed by the IP operator).
  
  When executing operators in an `OperatorContainer` it is important to first to ensure
  that all necessary computed vectors have been evaluated (and in the correct order).
  To help with this, OperatorContainer returns a set of all of the computed vectors
  on which operators in this `OperatorContainer` depend through the 
  `computedVectorsNeedingPrecalculation` method.
  
  Do write the code that will actually evaluate the operators, just call one of the ``evaluate*``
  functions. If you need to call another function on the operators other than ``evaluate``,
  (currently the only other function is ``calculateOperatorField``) then you would use the
  ``callOperatorFunctionWithArguments`` method.
  """
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
  
  
  def evaluateIPOperators(self, arguments = None, parentFunction = None):
    arguments = arguments or {}
    return self.callOperatorFunctionWithArguments('evaluate', self.ipOperators, arguments, parentFunction)
  
  def evaluatePreDeltaAOperators(self, arguments = None, parentFunction = None):
    arguments = arguments or {}
    return self.callOperatorFunctionWithArguments('evaluate', self.preDeltaAOperators, arguments, parentFunction)
  
  def evaluatePostDeltaAOperators(self, arguments = None, parentFunction = None):
    arguments = arguments or {}
    return self.callOperatorFunctionWithArguments('evaluate', self.postDeltaAOperators, arguments, parentFunction)
  
  def evaluateDeltaAOperator(self, arguments = None, parentFunction = None):
    arguments = arguments or {}
    if self.deltaAOperator:
      return self.callOperatorFunctionWithArguments('evaluate', [self.deltaAOperator], arguments, parentFunction)
    else:
      return ''
  
  def evaluateOperators(self, arguments = None, parentFunction = None):
    arguments = arguments or {}
    assert not self.postDeltaAOperators and not self.deltaAOperator and not self.ipOperators
    return self.callOperatorFunctionWithArguments('evaluate', self.preDeltaAOperators, arguments, parentFunction)
  
  @staticmethod
  def callOperatorFunctionWithArguments(functionName, operators, arguments = None, parentFunction = None):
    arguments = arguments or {}
    return '\n'.join(['// ' + op.description() + '\n' + op.functions[functionName].call(arguments, parentFunction = parentFunction) + '\n' for op in operators])
  
  def initialise(self):
    return '\n'.join([op.initialise() for op in self.operators])
  
  def finalise(self):
    return '\n'.join([op.finalise() for op in self.operators])
  
  
  def preflight(self):
    super(OperatorContainer, self).preflight()
    
    if self.field and self.deltaAOperator:
      assert self.field == self.deltaAOperator.field
    

