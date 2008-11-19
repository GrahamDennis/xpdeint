#!/usr/bin/env python
# encoding: utf-8
"""
FriendlyPlusStyle.py

Created by Graham Dennis on 2008-11-18.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from pygments.styles.friendly import FriendlyStyle
from pygments.token import String

class FriendlyPlusStyle(FriendlyStyle):
  """
  Slight modification of the Friendly style to make attribute-string values
  have different colours.
  """
  
  styles = FriendlyStyle.styles.copy()
  styles.update({String: "italic #517918"})
  
