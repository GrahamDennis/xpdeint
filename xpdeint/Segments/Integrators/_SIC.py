#!/usr/bin/env python
# encoding: utf-8
"""
_SIC.py

Created by Graham Dennis on 2008-08-06.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Segments.Integrators.FixedStep import FixedStep

from xpdeint.Operators.CrossPropagationOperator import CrossPropagationOperator

from xpdeint.ParserException import ParserException

class _SIC (FixedStep):
  def __init__(self, *args, **KWs):
    FixedStep.__init__(self, *args, **KWs)
    
    self.operatorContainerToOverride = None
    self.leftDeltaAOperator = None
    self.rightDeltaAOperator = None
    
    functionNamePrefix = '_' + self.id
    
    self.functions['leftDeltaA'] = Function(name = functionNamePrefix + '_calculate_left_delta_a',
                                            args = [('double', '_step')], 
                                            implementation = self.leftDeltaAFunctionBody)
    self.functions['rightDeltaA'] = Function(name = functionNamePrefix + '_calculate_left_delta_a',
                                             args = [('double', '_step')], 
                                             implementation = self.rightDeltaAFunctionBody)
    
  
  def leftDeltaAFunctionBody(self, function):
    return self.leftRightDeltaAFunctionBody(function, self.leftDeltaAOperator)
  
  def rightDeltaAFunctionBody(self, function):
    return self.leftRightDeltaAFunctionBody(function, self.rightDeltaAOperator)
  
  def leftRightDeltaAOperatorFromCrossPropagationOperator(self, crossOp):
    pass
  
  def preflight(self):
    super(FixedStep, self).preflight()
    
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
        if crossOp.propagationDirection == '+':
          # Propagating from left
          if self.leftDeltaAOperator:
            raise ParserException(self.xmlElement, "This integrator has two cross-propagators with left boundary conditions.\n"
                                                   "The SIC integrator can only have two cross-propagators, one in each direction of a single dimension.")
          self.leftDeltaAOperator = self.leftRightDeltaAOperatorFromCrossPropagationOperator(crossOp)
        else:
          # Propagating from right
          if self.rightDeltaAOperator:
            raise ParserException(self.xmlElement, "This integrator has two cross-propagators with right boundary conditions.\n"
                                                   "The SIC integrator can only have two cross-propagators, one in each direction of a single dimension.")
          self.rightDeltaAOperator = self.leftRightDeltaAOperatorFromCrossPropagationOperator(crossOp)
        
        if self.operatorContainerToOverride and not oc == self.operatorContainerToOverride:
          raise ParserException(self.xmlElement, "This integrator can only have at most two cross-propagators.\n"
                                                 "They must be in opposite directions, and be in the same <operators> block.")
        self.operatorContainerToOverride = oc
  
  

