#!/usr/bin/env python
# encoding: utf-8
"""
OperatorContainer.py

Created by Graham Dennis on 2008-03-09.

Copyright (c) 2008-2012, Graham Dennis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

from xpdeint.ScriptElement import ScriptElement

from xpdeint.Operators._Operator import _Operator
from xpdeint.ParserException import ParserException

from xpdeint.Utilities import lazy_property, valueForKeyPath

class _OperatorContainer(ScriptElement):
  """
  The `_OperatorContainer` is, as the name suggests, a container for operators.
  The idea is that there are many places where you want to be able to have a set
  of operators and you want to be execute all of them without worrying too much
  about what operators they are. 
  
  Similarly, some operators depend on a common (or 'shared') code block to determine
  their behaviour (e.g. IP and EX). The `OperatorContainer` abstracts exactly where
  this shared code block is and what its dependencies are so the operators don't need
  to know whether they are being used in an integrator or in moment group sampling,
  all they care about is that the `OperatorContainer` has been configured correctly.
  
  Configuring an OperatorContainer amounts to setting the `sharedCodeEntityKeyPath`, 
  `dependenciesKeyPath` and `sharedCodeSpaceKeyPath` variables in the initialiser
  for `OperatorContainer`. `sharedCodeEntityKeyPath` is a string that is a dotted-name
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
  `dynamicVectorsNeedingPrecalculation` method.
  
  Do write the code that will actually evaluate the operators, just call one of the ``evaluate*``
  functions. If you need to call another function on the operators other than ``evaluate``,
  (currently the only other function is ``calculateOperatorField``) then you would use the
  ``callOperatorFunctionWithArguments`` method.
  """
  def __init__(self, *args, **KWs):
    localKWs = self.extractLocalKWs(['field', 'name', 'sharedCodeBlockKeyPath'], KWs)
    
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default state
    self.ipOperators = []
    self.preDeltaAOperators = []
    self.ipOperatorBasis = None
    self.deltaAOperator = None
    self.postDeltaAOperators = []
    self.field = localKWs.get('field', None)
    self._name = localKWs.get('name', None)
    
    # These key paths are the 'paths' to the actual attributes for our
    # 'sharedCodeBlock' proxy property
    self.sharedCodeBlockKeyPath = localKWs.get('sharedCodeBlockKeyPath', 'deltaAOperator.primaryCodeBlock')
  
  def _getSharedCode(self):
    return valueForKeyPath(self, self.sharedCodeEntityKeyPath).value
  
  def _setSharedCode(self, value):
    valueForKeyPath(self, self.sharedCodeEntityKeyPath).value = value
  
  sharedCode = property(_getSharedCode, _setSharedCode)
  del _getSharedCode, _setSharedCode
  
  @lazy_property
  def sharedCodeBlock(self):
    return valueForKeyPath(self, self.sharedCodeBlockKeyPath)
  
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
    children = super(_OperatorContainer, self).children
    children.extend(self.operators)
    return children
  
  @property
  def dynamicVectorsNeedingPrecalculation(self):
    result = set()
    for operator in self.operators:
      result.update(operator.dynamicVectorsNeedingPrecalculation)
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
  
  def evaluateIPOperators(self, arguments = None, parentFunction = None, **KWs):
    arguments = arguments or {}
    return self.callOperatorFunctionWithArguments('evaluate', self.ipOperators, arguments, parentFunction, **KWs)
  
  def evaluatePreDeltaAOperators(self, arguments = None, parentFunction = None, **KWs):
    arguments = arguments or {}
    return self.callOperatorFunctionWithArguments('evaluate', self.preDeltaAOperators, arguments, parentFunction, **KWs)
  
  def evaluatePostDeltaAOperators(self, arguments = None, parentFunction = None, **KWs):
    arguments = arguments or {}
    return self.callOperatorFunctionWithArguments('evaluate', self.postDeltaAOperators, arguments, parentFunction, **KWs)
  
  def evaluateDeltaAOperator(self, arguments = None, parentFunction = None, **KWs):
    arguments = arguments or {}
    if self.deltaAOperator:
      return self.callOperatorFunctionWithArguments('evaluate', [self.deltaAOperator], arguments, parentFunction, **KWs)
    else:
      return ''
  
  def evaluateOperators(self, arguments = None, parentFunction = None, **KWs):
    arguments = arguments or {}
    assert not self.postDeltaAOperators and not self.deltaAOperator and not self.ipOperators
    return self.callOperatorFunctionWithArguments('evaluate', self.preDeltaAOperators, arguments, parentFunction, **KWs)
  
  @staticmethod
  def callOperatorFunctionWithArguments(functionName, operators, arguments = None, parentFunction = None, **KWs):
    arguments = arguments or {}
    return '\n'.join(['// ' + op.description() + '\n' + op.functions[functionName].call(arguments, parentFunction = parentFunction, **KWs) + '\n' for op in operators])
  
  def preflight(self):
    super(_OperatorContainer, self).preflight()
    
    if self.field and self.deltaAOperator:
      assert self.field == self.deltaAOperator.field
    
    if self.ipOperators:
      ipOperatorBasisSet = set()
      ipOperatorDimensionNames = set()
      for ipOperator in self.ipOperators:
        assert not ipOperator.resultVector
        operatorBasis = ipOperator.field.basisForBasis(ipOperator.operatorBasis)
        for dim in ipOperator.field.dimensions:
          if dim.name in ipOperatorDimensionNames and not dim.inBasis(operatorBasis).name in ipOperatorBasisSet:
            raise ParserException(ipOperator.xmlElement,
            "The basis for this IP operator (%s) conflicts with that of a previous IP operator.  "
            "For example, it isn't possible to have one IP operator acting in the 'x' basis and another in the 'kx' basis."
            % ', '.join(operatorBasis))
        
          ipOperatorDimensionNames.add(dim.name)
          ipOperatorBasisSet.add(dim.inBasis(operatorBasis).name)
      self.ipOperatorBasis = self.field.completedBasisForBasis(tuple(ipOperatorBasisSet), self.field.defaultSpectralBasis)
      vectorsRequiredForIPOperation = set()
      for ipOperator in self.ipOperators:
        vectorsRequiredForIPOperation.update(ipOperator.targetVectors)
        vectorsRequiredForIPOperation.add(ipOperator.operatorVector)
      self.registerVectorsRequiredInBasis(vectorsRequiredForIPOperation, self.ipOperatorBasis)

