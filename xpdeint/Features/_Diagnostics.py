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
    dimReps = dict['dimReps']
    
    if not any(dimRep.type == 'long' and isinstance(dimRep, UniformDimensionRepresentation) for dimRep in dimReps):
      return
    
    vector = dict['vector']
    nonlocalAccessVariableName = dict['nonlocalAccessVariableName']
    nonlocalAccessString = dict['nonlocalAccessString']
    componentName = dict['componentName']
    
    args = [(dimRep.type, dimRep.loopIndex) for dimRep in dimReps]
    args.extend([('const char*', 'filename'), ('int', 'line_number')])
    
    implementation = lambda func: self.nonlocalAccessValidationFunctionContents(dimReps, nonlocalAccessString, componentName, func)
    
    self.functions[nonlocalAccessVariableName] = Function(
      '_' + nonlocalAccessVariableName,
      args,
      implementation,
      returnType = 'inline ' + vector.type + '&',
    )
    
    argumentsString = ', '.join(dimRep.loopIndex for dimRep in dimReps)
    defineString = '#define %(nonlocalAccessVariableName)s(%(argumentsString)s) _%(nonlocalAccessVariableName)s(%(argumentsString)s, __FILE__, __LINE__)\n' % locals()
    dict['defineString'] = defineString
