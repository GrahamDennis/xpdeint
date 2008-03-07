#!/usr/bin/env python
# encoding: utf-8
"""
_GaussianDSFMTNoise.py

Created by Graham Dennis on 2008-03-07.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from DSFMTNoise import DSFMTNoise
from GaussianBoxMuellerNoiseMethod import GaussianBoxMuellerNoiseMethod

class _GaussianDSFMTNoise(DSFMTNoise, GaussianBoxMuellerNoiseMethod):
  # Because generated Cheetah templates directly call their superclass' __init__ function
  # and don't use super(), we must also follow this convention.
  # See http://fuhm.net/super-harmful/ for more info about dealing with diamond inheritence safely.
  # Fortunately for us, Template makes sure that it isn't doubly-initialised.
  def __init__(self, *args, **KWs):
    DSFMTNoise.__init__(self, *args, **KWs)
    GaussianBoxMuellerNoiseMethod.__init__(self, *args, **KWs)
  
