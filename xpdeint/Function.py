#!/usr/bin/env python
# encoding: utf-8
"""
Function.py

Created by Graham Dennis on 2008-07-10.

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

class Function(object):
  """
  The idea behind Function objects is that they wrap C functions that will be in
  the generated source file that will need to be flexible in terms of what
  arguments they have. This way, one object can add function arguments to the
  functions 'belonging' to other objects without the second object needing to be
  involved.

  An example of an application of this is passing the cross-propagation dimension
  variable to delta-a operators in the cross-propagation integrator. As the
  cross-propagation integrator is a normal integrator, it wouldn't normally need
  to pass the propagation dimension variable to the delta a operator as the
  propagation dimension value is stored in a global variable. With the function
  objects, the cross-propagation operator just needs to add additional arguments
  to the cross-propagation delta-a calculation function and the delta-a operator
  and these variables are then passed through these functions.

  In a similar way other variables like cycle number of a looping segment could
  be passed to children if a use for that can be found. This behaviour was
  present in xmds-1, but hasn't been added to xpdeint as there hasn't been a need
  for it, and it isn't clear how this behaviour would work in the face of nested
  looping segments.
  """
  def __init__(self, name, args, implementation,
               description = None, returnType = 'void', predicate = lambda: True):
    """
    Initialise a `Function` object with C name `functionName`, arguments `args` and a
    return type of `returnType`. The `implementation` argument must be a function that
    returns the body of the C function.
    
    The `args` argument is an array of 2-tuples of the form ``('argType', 'argName')``.
    
    `predicate` is a callable that will cause the function not to be defined if it returns false
    """
    self.name = name
    self.args = args[:]
    self.implementationContents = implementation
    self.returnType = returnType
    self.description = description
    # Note that the predicate is actually used by _ScriptElement
    self.predicate = predicate
  
  def _prototype(self):
    """
    Return as a string the C function prototype that can be used for both
    function declaration and definition.
    
    For example, return ``void _segment3(int myInt)``.
    """
    argumentString = ', '.join([arg[0] + ' ' + arg[1] for arg in self.args])
    return ''.join([self.returnType, ' ', self.name, '(', argumentString, ')'])
  
  def prototype(self):
    """
    Return as a string the C function prototype for this function.
    
    For example, return ``void _segment3(int myInt);\\n``.
    """
    return self._prototype() + ';\n'
  
  def implementation(self):
    """
    Return as a string the C function implementation for this function.
    """
    implementationBodyString = self.implementationContents(self)
    result = []
    if self.description:
      result.append('// ' + self.description + '\n')
    result.extend([self._prototype(), '\n{\n'])
    for line in implementationBodyString.splitlines(True):
      result.extend(['  ', line])
    result.append('}\n')
    return ''.join(result)
  
  def call(self, arguments = None, parentFunction = None, **KWs):
    """
    Return as a string the C code to call this function with arguments `arguments`
    and any keyword arguments.
    """
    availableArguments = {}
    # The precendence for the arguments is KWs, arguments, parentFunction.
    # So we add arguments to availableArguments in the opposite order.
    if parentFunction:
      availableArguments.update([(arg[1], arg[1]) for arg in parentFunction.args])
    if arguments:
      availableArguments.update(arguments)
    if KWs:
      availableArguments.update(KWs)
    argumentString = ', '.join([str(availableArguments[arg[1]]) for arg in self.args])
    return ''.join([self.name, '(', argumentString, ');'])
  
