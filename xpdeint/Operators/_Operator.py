#!/usr/bin/env python
# encoding: utf-8
"""
_Operator.py

This contains all the pure-python code for Operator.tmpl

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement
from xpdeint.ParserException import ParserException

from xpdeint import RegularExpressionStrings
import re

from xpdeint.Function import Function

class _Operator (ScriptElement):
  # This is an ordered list of (type, argName) pairs
  evaluateOperatorFunctionArguments = []
  
  # Operator kinds
  IPOperatorKind     = 1
  OtherOperatorKind  = 2
  DeltaAOperatorKind = 3
  
  operatorKind = OtherOperatorKind
  
  vectorsMustBeInSubsetsOfIntegrationField = True
  
  def __init__(self, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.dependenciesEntity = None
    self.operatorComponents = {}
    self.operatorVector = None
    self.resultVector = None
    self.operatorNumber = -1
    self._field = None
    self._children = []
    self._loopingField = None
    self.loopingOrder = ScriptElement.LoopingOrder.MemoryOrder
    
    parent = self.parent
    parent.addOperator(self)
    evaluateOperatorFunctionName = ''.join(['_', parent.id, '_evaluate_', self.name])
    evaluateOperatorFunction = Function(name = evaluateOperatorFunctionName,
                                        args = self.evaluateOperatorFunctionArguments,
                                        implementation = self.evaluateOperatorFunctionContents,
                                        description = self.description())
    self.functions['evaluate'] = evaluateOperatorFunction
    if hasattr(self, 'calculateOperatorFieldFunctionArguments'):
      calculateOperatorFieldFunctionName = ''.join(['_', parent.id, '_calculate_', self.name, '_field'])
      calculateOperatorFieldFunction = Function(name = calculateOperatorFieldFunctionName, 
                                                args = self.calculateOperatorFieldFunctionArguments,
                                                implementation = self.calculateOperatorFieldFunctionContents,
                                                description = self.description())
      self.functions['calculateOperatorField'] = calculateOperatorFieldFunction
    
  
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
  def targetVectors(self):
    targetVectors = set()
    
    # Loop over the vectors that the operators are going to operate on
    for targetVectorDict in self.operatorComponents.itervalues():
      targetVectors.update(set(targetVectorDict.keys()))
    
    return targetVectors
  
  @property
  def defaultOperatorSpace(self):
    return self.field.spaceMask
  
  @property
  def calculateOperatorFieldFunctionArgumentString(self):
    return ', '.join([pair[0] + ' ' + pair[1] for pair in self.calculateOperatorFieldFunctionArguments])
  
  @property
  def evaluateOperatorFunctionArgumentString(self):
    return ', '.join([pair[0] + ' ' + pair[1] for pair in self.evaluateOperatorFunctionArguments])
  
  @property
  def computedVectorsNeedingPrecalculation(self):
    return filter(lambda x: x.isComputed, self.dependencies)
  
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
  
  
  def _getField(self):
    if self._field:
      return self._field
    else:
      return self.parent.field
  
  def _setField(self, value):
    self._field = value
  
  field = property(_getField, _setField)
  del _getField, _setField
  
  def targetComponentsForOperatorsInString(self, operatorNames, propagationCode):
    operatorCodeRegex = re.compile(r'\b(' + '|'.join(operatorNames) + ')'+ RegularExpressionStrings.threeLevelsMatchedSquareBrackets, re.VERBOSE)
    return operatorCodeRegex.findall(propagationCode)
  
  
  def bindNamedVectors(self):
    super(_Operator, self).bindNamedVectors()
    
    if self.resultVector:
      self.resultVector.spacesNeeded.add(self.operatorSpace)
  
  def preflight(self):
    super(_Operator, self).preflight()
    
    if self.dependenciesEntity:
      for dependency in self.dependencies:
        if self.vectorsMustBeInSubsetsOfIntegrationField and not dependency.field.isSubsetOfField(self.field):
          raise ParserException(self.dependenciesEntity.xmlElement,
                  "Can't depend on a vector that is in a field that has dimensions that "
                  "aren't in this field (%s).\n"
                  "The vector causing this problem is '%s'." 
                  % (self.field.name, dependency.name))
    
    
  
