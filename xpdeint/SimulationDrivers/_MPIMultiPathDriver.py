#!/usr/bin/env python
# encoding: utf-8
"""
_MPIMultiPathDriver.py

Created by Graham Dennis on 2008-03-28.

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

from xpdeint.SimulationDrivers.MultiPathDriver import MultiPathDriver
from xpdeint.SimulationDrivers.MPI import MPI

class _MPIMultiPathDriver (MultiPathDriver, MPI):
  def __init__(self, *args, **KWs):
    MultiPathDriver.__init__(self, *args, **KWs)
    MPI.__init__(self, *args, **KWs)
  
