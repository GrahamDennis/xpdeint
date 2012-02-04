#!/usr/bin/env python
# encoding: utf-8
"""
_FixedStepWithCross.py

Created by Graham Dennis on 2008-08-06.

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

from xpdeint.Segments.Integrators.FixedStep import FixedStep

from xpdeint.Operators.CrossPropagationOperator import CrossPropagationOperator
from xpdeint.Operators.OperatorContainer import OperatorContainer
from xpdeint.Operators.SICDeltaAOperator import SICDeltaAOperator

from xpdeint.ParserException import ParserException
from xpdeint.Function import Function
from xpdeint.Geometry import FieldElement

class _FixedStepWithCross (FixedStep):
  def __init__(self, *args, **KWs):
    FixedStep.__init__(self, *args, **KWs)
    
    self.operatorContainerToOverride = None
    self.leftOperatorContainer = None
    self.rightOperatorContainer = None
    self.leftRightLoopingField = None
    
    functionNamePrefix = '_' + self.id
    
    self.functions['leftDeltaA'] = Function(name = functionNamePrefix + '_calculate_left_delta_a',
                                            args = [('real', '_step')], 
                                            implementation = self.leftDeltaAFunctionBody,
                                            predicate = lambda: bool(self.leftOperatorContainer))
    self.functions['rightDeltaA'] = Function(name = functionNamePrefix + '_calculate_right_delta_a',
                                             args = [('real', '_step')], 
                                             implementation = self.rightDeltaAFunctionBody,
                                             predicate = lambda: bool(self.rightOperatorContainer))
    
  
  def leftDeltaAFunctionBody(self, function):
    return self.leftRightDeltaAFunctionBody(function, self.leftOperatorContainer)
  
  def rightDeltaAFunctionBody(self, function):
    return self.leftRightDeltaAFunctionBody(function, self.rightOperatorContainer)
  
  def leftRightOperatorContainerFromCrossPropagationOperator(self, crossOp):
    # We can just extract the Delta-a operator from the cross-propagation integrator
    # and then modify the inner code somewhat, and we're done.
    # We may need to reorder the looping dimensions in order to get the cross-propagation dimension
    # looped across last.... Is this safe, combined with integer-valued dimension stuff?
    # How about we just assert that its current loopingField is the same as the operator field.
    # Nope. It's in preflight() that the DeltaA operator reorders its dimensions... but we can make
    # it not do that if loopingField has already been set. (and raise an exception)
    direction = crossOp.propagationDirection
    if direction == '+':
      directionName = 'left'
    else:
      directionName = 'right'
    
    oldCrossDeltaAOperator = crossOp.crossPropagationIntegratorDeltaAOperator
    normalDeltaAOperator = self.operatorContainerToOverride.deltaAOperator
    
    operatorContainer = OperatorContainer(field = self.operatorContainerToOverride.field,
                                          parent = self,
                                          name = directionName + '_container',
                                          **self.argumentsToTemplateConstructors)
    
    leftRightDeltaAOperator = SICDeltaAOperator(parent = operatorContainer,
                                                **self.argumentsToTemplateConstructors)
    leftRightDeltaAOperator.crossPropagationDimension           = crossOp.propagationDimension
    leftRightDeltaAOperator.crossPropagationDirection           = direction
    leftRightDeltaAOperator.integrationVectorsEntity            = normalDeltaAOperator.integrationVectorsEntity
    leftRightDeltaAOperator.codeBlocks['operatorDefinition']    = normalDeltaAOperator.codeBlocks['operatorDefinition']
    
    leftRightDeltaAOperator.codeBlocks['boundaryCondition']     = crossOp.codeBlocks['boundaryCondition']
    
    leftRightDeltaAOperator.crossIntegrationVectorsEntity       = crossOp.integrationVectorsEntity
    leftRightDeltaAOperator.codeBlocks['crossPropagation']      = oldCrossDeltaAOperator.codeBlocks['operatorDefinition']
    
    leftRightDeltaAOperator.iterations = crossOp.crossPropagationIntegrator.stepper.iterations
    
    # Now we need to work out if we need to create a new field to be the looping field
    crossPropagationDimensionName = crossOp.propagationDimension
    if not self.leftRightLoopingField:
      if leftRightDeltaAOperator.field.dimensions[-1].name != crossPropagationDimensionName:
        # We need to create a new field with reordered dimensions
        loopingFieldName = ''.join(['_', normalDeltaAOperator.id, '_leftright_looping_field'])
        
        loopingField = FieldElement(name = loopingFieldName,
                                    **self.argumentsToTemplateConstructors)
        
        loopingField.dimensions = [dim.copy(parent=loopingField) for dim in newFieldDimensions]
        crossDim = loopingField.dimensionWithName(crossPropagationDimensionName)
        loopingField.dimensions.remove(crossDim)
        loopingField.dimensions.append(crossDim)
        self.leftRightLoopingField = loopingField
      else:
        # We set this to prevent the delta-a operator itself trying to change its looping field.
        self.leftRightLoopingField = leftRightDeltaAOperator.field
    leftRightDeltaAOperator.loopingField = self.leftRightLoopingField
    
    self._children.append(operatorContainer)
    return operatorContainer
  
  def bindNamedVectors(self):
    super(_FixedStepWithCross, self).bindNamedVectors()
    
    # This needs to go in bindNamedVectors not preflight because the CrossPropagationOperator
    # fiddles with the mapping of vector names to vectors for its child elements, and it will be annoying
    # to undo, so we best clear out all of these objects before that happens.
    
    # Now we need to drill down into our operator container objects, locate the cross-propagators (there should be some)
    # and then destroy them and copy their code into our left- and right-propagating delta-a objects. But destroying a
    # cross-propagator is quite involved as it requires destroying the actual integration objects too. Let's hope that
    # our 'remove' method works correctly.
    
    propagationDimension = None
    
    for oc in self.intraStepOperatorContainers:
      crossOperators = [op for op in oc.preDeltaAOperators if isinstance(op, CrossPropagationOperator)]
      for crossOp in crossOperators:
        if not propagationDimension:
          propagationDimension = crossOp.propagationDimension
        if self.operatorContainerToOverride and not oc == self.operatorContainerToOverride:
          raise ParserException(self.xmlElement, "This integrator can only have at most two cross-propagators. "
                                                 "They must be in opposite directions, and be in the same <operators> block.")
        self.operatorContainerToOverride = oc
        if crossOp.propagationDirection == '+':
          # Propagating from left
          if self.leftOperatorContainer:
            raise ParserException(self.xmlElement, "This integrator has two cross-propagators with left boundary conditions. "
                                                   "The SIC integrator can only have two cross-propagators, one in each direction of a single dimension.")
          self.leftOperatorContainer = self.leftRightOperatorContainerFromCrossPropagationOperator(crossOp)
        else:
          # Propagating from right
          if self.rightOperatorContainer:
            raise ParserException(self.xmlElement, "This integrator has two cross-propagators with right boundary conditions. "
                                                   "The SIC integrator can only have two cross-propagators, one in each direction of a single dimension.")
          self.rightOperatorContainer = self.leftRightOperatorContainerFromCrossPropagationOperator(crossOp)
        
        # Kill the CrossPropagationOperator and its children
        oc.preDeltaAOperators.remove(crossOp)
        crossOp.remove()
    
  def preflight(self):
    super(_FixedStepWithCross, self).preflight()
    
    if not self.leftOperatorContainer and not self.rightOperatorContainer:
      raise ParserException(self.xmlElement, "It doesn't make sense to use the 'SIC' integrator without any cross-propagation operators. Use 'SI' instead.")
    
    for oc in [self.leftOperatorContainer, self.rightOperatorContainer]:
      if not oc:
        continue
      self.operatorContainerToOverride.deltaAOperator.dependencies.update(oc.deltaAOperator.crossIntegrationVectors)


