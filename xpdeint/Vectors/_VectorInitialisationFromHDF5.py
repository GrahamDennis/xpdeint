#!/usr/bin/env python
# encoding: utf-8
"""
_VectorInitialisationFromHDF5.py

Created by Graham Dennis on 2009-01-31.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Vectors.VectorInitialisation import VectorInitialisation
from xpdeint.Features.HDF5 import HDF5

class _VectorInitialisationFromHDF5 (VectorInitialisation, HDF5):
  def __init__(self, *args, **KWs):
    VectorInitialisation.__init__(self, *args, **KWs)
    HDF5.__init__(self, *args, **KWs)
  
