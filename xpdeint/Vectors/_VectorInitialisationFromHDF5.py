#!/usr/bin/env python
# encoding: utf-8
"""
_VectorInitialisationFromHDF5.py

Created by Graham Dennis on 2009-01-31.

Copyright (c) 2009-2012, Graham Dennis

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

from xpdeint.Vectors.VectorInitialisation import VectorInitialisation
from xpdeint.HDF5 import HDF5

class _VectorInitialisationFromHDF5 (VectorInitialisation, HDF5):
  def __init__(self, *args, **KWs):
    VectorInitialisation.__init__(self, *args, **KWs)
    HDF5.__init__(self, *args, **KWs)
  
