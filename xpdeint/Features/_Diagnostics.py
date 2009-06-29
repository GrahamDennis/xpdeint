#!/usr/bin/env python
# encoding: utf-8
"""
_Diagnostics.py

Created by Graham Dennis on 2009-06-15.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature

from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Function import Function

class _Diagnostics (_Feature):
  def nonlocalAccess(self, dict):
    """
    The purpose of this function is to safety-check nonlocal dimension access. The only place where this is potentially
    unsafe is with integer-valued dimensions as we permit users to use any code to access a dimension. For speed reasons
    we don't run safety checks. But in the diagnostics feature, we can sacrifice speed for more safety.
    
    For any nonlocally-accessed dimReps, we replace the usual #define with a function call that includes the line number
    from which it was called from the original .xmds file. The function then does a bounds check on all potentially-unsafe
    accesses and stops the simulation if any are found.
    """
    availableDimReps = dict['availableDimReps']
    dimRepsNeeded = dict['dimRepsNeeded']
    
    if not any(dimRep.type == 'long' and isinstance(dimRep, UniformDimensionRepresentation) for dimRep in dimRepsNeeded):
      return
    
    vector = dict['vector']
    nonlocalAccessVariableName = dict['nonlocalAccessVariableName']
    nonlocalAccessString = dict['nonlocalAccessString']
    componentName = dict['componentName']
    
    args = [(dimRep.type, dimRep.loopIndex) for dimRep in availableDimReps]
    args.extend([('const char*', 'filename'), ('int', 'line_number')])
    
    implementation = lambda func: self.nonlocalAccessValidationFunctionContents(dimRepsNeeded, nonlocalAccessString, componentName, func)
    
    self.functions[nonlocalAccessVariableName] = Function(
      '_' + nonlocalAccessVariableName,
      args,
      implementation,
      returnType = 'inline ' + vector.type + '&',
    )
    
    defineArgumentsString = ', '.join(dimRep.loopIndex for dimRep in dimRepsNeeded)
    functionArgumentsString = ', '.join(dimRep.loopIndex for dimRep in availableDimReps)
    defineString = '#define %(nonlocalAccessVariableName)s(%(defineArgumentsString)s) _%(nonlocalAccessVariableName)s(%(functionArgumentsString)s, __FILE__, __LINE__)\n' % locals()
    dict['defineString'] = defineString
