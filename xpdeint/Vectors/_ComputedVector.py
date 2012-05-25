#!/usr/bin/env python
# encoding: utf-8
"""
_ComputedVector.py

This contains all the pure-python code for ComputedVector.tmpl

Created by Graham Dennis on 2008-03-12.

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

from xpdeint.Vectors.VectorElement import VectorElement

from xpdeint.Function import Function
from xpdeint.Utilities import lazy_property

class _ComputedVector (VectorElement):
  isComputed = True
  
  def __init__(self, *args, **KWs):
    VectorElement.__init__(self, *args, **KWs)
    
    # Set default variables
    
    # Computed vectors don't need explicit initialisation.  If we're integrating over components, VectorElement will automatically set the vector to zero.
    self._integratingComponents = False
    self.initialiser = None
    
    evaluateFunctionName = ''.join(['_', self.id, '_evaluate'])
    evaluateFunction = Function(name = evaluateFunctionName,
                               args = [],
                               implementation = self.evaluateFunctionContents)
    self.functions['evaluate'] = evaluateFunction
  
  @property
  def dependencies(self):
    return self.codeBlocks['evaluation'].dependencies
  
  @property
  def primaryCodeBlock(self):
    return self.codeBlocks['evaluation']
  

