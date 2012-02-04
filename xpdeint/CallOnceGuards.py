#!/usr/bin/env python
# encoding: utf-8
"""
CallOnceGuards.py

Created by Graham Dennis on 2007-12-14.

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


These function decorators are used to ensure that certain functions are only called
once during the generation of the simulation script. One example where these are used
is segment (e.g. an integrator) initialisation. If a segment is called multiple times
in a simulation, then it would be a good idea to perform all initialisation of the 
segment that doesn't change between invocations only once. A segment might be called
multiple times when we are performing a multi-path simulation, or if the segment
exists inside of a sequence that is looping.

One easy way to implement this optimisation is for anything that might be doing the looping
(which must be further up the call tree than the segment that is being looped over) to call
the initialisation code for the segment before the loop. To prevent the segment writing its
own initialisation code in the normal segment routine, there needs to be a way to prevent the
segment including this code. We could add flags for each of these functions, but it could be
quite easy to forget. Using function decorators, we can wrap the function that we only want
to execute once to check the value of a flag to see if it has executed before and return an
empty string if it has, but to execute and change the value of the flag if it hasn't. This way
the checking of the flag is built into the execution of the function itself.

As our 'preflight' stage of the simulation now includes a 'dry-run' stage that does a preliminary
conversion of the simulation classes to a C++ source file, we will need to be able to reset these
flags after the execution of the dry-run so that functions that were called during the dry-run do
not prevent those same functions being called during the actual conversion of the simulation
classes to the C++ source file. To achieve this, `_ScriptElement` has a `resetGuards` method that
resets all of the CallOnceGuards.

To use a CallOnceGuard, import this file into the Cheetah template or Python source file and then
use the decorator syntax (in Python)::

  @callOnceGuard
  def someFunction(self):
    doSomeStuff
    
    return "thingy"
  
Or in a Cheetah template::

  @@callOnceGuard
  @def someOtherFunction($someArgument)
    @# Put stuff here
  @end def

There are two function decorators provided by this module, `callOnceGuard` and `callOncePerInstanceGuard`.
The first, `callOnceGuard` prevents a function being called more than once, even if the call is made
on a different instance. This is useful for example for ensuring that a header has been ``#include``'ed
that might be required by multiple instances of a given class (e.g. the MKL noises). The second decorator,
`callOncePerInstanceGuard` is useful when you want a function to only be called once for a given instance.
This is useful in the example given above where a segment should only be initialised once.
"""

from functools import wraps
from xpdeint._ScriptElement import _ScriptElement


def callOnceGuard(f):
  """Function decorator to prevent a function being called more than once."""
  @wraps(f)
  def wrapper(*args, **KWs):
    # If the function object isn't in the guard set, then add it and run the function
    if not f in _ScriptElement._callOnceGuards:
      _ScriptElement._callOnceGuards.add(f)
      return f(*args, **KWs)
    else:
      return ''
  
  return wrapper


def callOncePerInstanceGuard(f):
  """Function decorator to prevent a function being called more than once for each instance."""
  @wraps(f)
  def wrapper(self, *args, **KWs):
    # If the guard name isn't in the guard set for this instance, then add it and run the function
    if not f in _ScriptElement._callOncePerInstanceGuards[self]:
      _ScriptElement._callOncePerInstanceGuards[self].add(f)
      return f(self, *args, **KWs)
    else:
      return ''
  
  return wrapper

