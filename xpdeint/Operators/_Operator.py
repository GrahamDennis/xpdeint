#!/usr/bin/env python
# encoding: utf-8
"""
_Operator.py

This contains all the pure-python code for Operator.tmpl

Created by Graham Dennis on 2007-10-18.

Copyright (c) 2007-2012, Graham Dennis

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
from xpdeint.ParserException import ParserException

from xpdeint.Function import Function
from xpdeint.Utilities import lazy_property
from xpdeint.CallOnceGuards import callOncePerInstanceGuard

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
    localKWs = self.extractLocalKWs(['name'], KWs)
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.dependenciesEntity = None
    self.operatorComponents = {}
    self.operatorVector = None
    self.resultVector = None
    self.operatorNumber = -1
    
    # the name is only used for filter operators, which default to a normal segment object if not named in the XML
    self._name = None
    if localKWs:
        self._name = localKWs['name']
    
    parent = self.parent
    parent.addOperator(self)
    if self._name:
        evaluateOperatorFunctionName = self._name
    else:
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
    children = super(_Operator, self).children
    children.extend(filter(lambda x: x, [self.operatorVector, self.resultVector]))
    return children
  
  @lazy_property
  def name(self):
    return 'operator' + str(self.operatorNumber)
  
  @property
  def targetVectors(self):
    targetVectors = set()
    
    # Loop over the vectors that the operators are going to operate on
    for targetVectorDict in self.operatorComponents.itervalues():
      targetVectors.update(set(targetVectorDict.keys()))
    
    return targetVectors
  
  @lazy_property
  def calculateOperatorFieldFunctionArgumentString(self):
    return ', '.join([pair[0] + ' ' + pair[1] for pair in self.calculateOperatorFieldFunctionArguments])
  
  @lazy_property
  def evaluateOperatorFunctionArgumentString(self):
    return ', '.join([pair[0] + ' ' + pair[1] for pair in self.evaluateOperatorFunctionArguments])
  
  @lazy_property
  def dynamicVectorsNeedingPrecalculation(self):
    vectorSet = self.dependencies.copy()
    vectorSet.update(self.targetVectors)
    return filter(lambda x: x.isComputed or x.isNoise, vectorSet)
  
  @lazy_property
  def primaryCodeBlock(self):
    return self.codeBlocks['operatorDefinition']
  
  @property
  def dependencies(self):
    return self.primaryCodeBlock.dependencies
  
  @property
  def operatorBasis(self):
    return self.primaryCodeBlock.basis
  
  @lazy_property
  def field(self):
    return self.parent.field
  
  def preflight(self):
    super(_Operator, self).preflight()
    
    if self.primaryCodeBlock.dependenciesEntity:
      # If this operator has dependencies, then the integrator cannot be initialised early.
      # This only affects the multi-path drivers, which try to initialise integrators once
      # per node, rather than once per path.  The following code disables this optimisation
      # in this situation
      if self.operatorVector:
        self.parent.parent.canBeInitialisedEarly = False
      for dependency in self.primaryCodeBlock.dependencies:
        if self.vectorsMustBeInSubsetsOfIntegrationField and not dependency.field.isSubsetOfField(self.field):
          raise ParserException(self.primaryCodeBlock.dependenciesEntity.xmlElement,
                  "Can't depend on a vector that is in a field that has dimensions that "
                  "aren't in this field (%s).\n"
                  "The vector causing this problem is '%s'." 
                  % (self.field.name, dependency.name))
    
  
  @callOncePerInstanceGuard
  def allocate(self):   return super(_Operator, self).allocate()
  @callOncePerInstanceGuard
  def free(self):       return super(_Operator, self).free()
  
  @callOncePerInstanceGuard
  def initialise(self): return super(_Operator, self).initialise()
  @callOncePerInstanceGuard
  def finalise(self):   return super(_Operator, self).finalise()
  
  
