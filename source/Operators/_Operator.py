#!/usr/bin/env python
# encoding: utf-8
"""
_Operator.py

This contains all the pure-python code for Operator.tmpl

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from .ScriptElement import ScriptElement
from ParserException import ParserException

import RegularExpressionStrings
import re

class _Operator (ScriptElement):
  evaluateOperatorFunctionArgument = 'double _step'
  
  # Operator kinds
  IPOperatorKind     = 1
  OtherOperatorKind  = 2
  DeltaAOperatorKind = 3
  
  operatorKind = OtherOperatorKind
  
  vectorsMustBeInSubsetsOfIntegrationField = True
  
  calculateOperatorFieldFunctionArguments = ''
  
  def __init__(self, parent, *args, **KWs):
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.dependenciesEntity = None
    self.operatorComponents = {}
    self.operatorVector = None
    self.resultVector = None
    self.operatorNumber = -1
    self._parent = parent
    parent.addOperator(self)
    self._field = None
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
    
    if self.dependenciesEntity:
      dependencies = self.vectorsFromEntity(self.dependenciesEntity)
      
      for dependency in dependencies:
        if self.vectorsMustBeInSubsetsOfIntegrationField and not dependency.field.isSubsetOfField(self.field):
          raise ParserException(self.dependenciesEntity.xmlElement,
                  "Can't depend on a vector that is in a field that has dimensions that "
                  "aren't in this field (%s).\n"
                  "The vector causing this problem is '%s'." 
                  % (self.field.name, dependency.vector.name))
        
        # If the vector is computed, we need to run a check that we are able to access this vector.
        if dependency.isComputed:
          # We can access it if its parent is its field, or if its parent is our container's parent
          operatorContainer = self.parent
          if not dependency.parent in (dependency.field, operatorContainer.parent):
            raise ParserException(self.dependenciesEntity.xmlElement,
                    "The computed vector '%s' cannot be accessed here.\n"
                    "The computed vector must be moved into the <integrator> element for this operator or\n"
                    "into a <field> element at the top of the simulation script." % dependency.name)
      
      self.dependencies.update(dependencies)
    
    if self.resultVector:
      self.resultVector.spacesNeeded.add(self.operatorSpace)
  
  
