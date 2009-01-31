#!/usr/bin/env python
# encoding: utf-8
"""
_HDF5Format.py

Created by Graham Dennis on 2009-01-31.
Copyright (c) 2009 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features.OutputFormat import OutputFormat
from xpdeint.Features.HDF5 import HDF5

class _HDF5Format (OutputFormat, HDF5):
  def __init__(self, *args, **KWs):
    OutputFormat.__init__(self, *args, **KWs)
    HDF5.__init__(self, *args, **KWs)
  
