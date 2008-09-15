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
from xpdeint.Utilities import lazyproperty

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
    self._children = []
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
  
  @lazyproperty
  def name(self):
    return 'operator' + str(self.operatorNumber)
  
  @lazyproperty
  def targetVectors(self):
    targetVectors = set()
    
    # Loop over the vectors that the operators are going to operate on
    for targetVectorDict in self.operatorComponents.itervalues():
      targetVectors.update(set(targetVectorDict.keys()))
    
    return targetVectors
  
  @lazyproperty
  def defaultOperatorSpace(self):
    return self.field.spaceMask
  
  @lazyproperty
  def calculateOperatorFieldFunctionArgumentString(self):
    return ', '.join([pair[0] + ' ' + pair[1] for pair in self.calculateOperatorFieldFunctionArguments])
  
  @lazyproperty
  def evaluateOperatorFunctionArgumentString(self):
    return ', '.join([pair[0] + ' ' + pair[1] for pair in self.evaluateOperatorFunctionArguments])
  
  @lazyproperty
  def computedVectorsNeedingPrecalculation(self):
    return filter(lambda x: x.isComputed, self.dependencies)
  
  @lazyproperty
  def operatorSpace(self):
    return self.defaultOperatorSpace
  
  @lazyproperty
  def loopingField(self):
    return self.field
  
  @lazyproperty
  def field(self):
    return self.parent.field
  
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
    
    
  
