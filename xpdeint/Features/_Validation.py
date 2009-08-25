#!/usr/bin/env python
# encoding: utf-8
"""
_Validation.py

Created by Graham Dennis on 2008-03-21.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature

import textwrap

class _Validation (_Feature):
  def __init__(self, *args, **KWs):
    localKWs = self.extractLocalKWs(['runValidationChecks'], KWs)
    
    _Feature.__init__(self, *args, **KWs)
    
    self.validationChecks = []
    self.runValidationChecks = localKWs.get('runValidationChecks', True)
  
  def preflight(self):
    super(_Validation, self).preflight()
    
    self.validationChecks = [textwrap.dedent(check) for check in self.validationChecks]
  
