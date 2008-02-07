#!/usr/bin/env python
# encoding: utf-8
"""
AutoVectorise.py

Created by Graham Dennis on 2008-02-07.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from _Feature import _Feature

import re

class _AutoVectoriseFeature (_Feature):
  def loopOverVectorsWithInnerContentTemplateModifyTemplate(self, dict):
    """
    Modifies the `templateString` to add in auto-vectorisation features.
    
    This function is called from ScriptElement's loopOverVectorsWithInnerContentTemplate.
    """
    templateString = dict['templateString']
    
    if 'UNVECTORISABLE' in templateString:
      return
    
    # Assert that no-one has touched the loopCountPrefixFunction because I can't
    # think of a possible way to make multiple bits of code that want to modify
    # this function work safely together. If such a need ever arises, then the
    # problem can be solved then, and it will be picked up thanks to this assert.
    assert dict['loopCountPrefixFunction'] == None
    
    def loopCountPrefixFunction(vector):
      if vector.type == 'complex':
        return '2 * '
      else:
        return ''
    
    dict['loopCountPrefixFunction'] = loopCountPrefixFunction
    
    newTemplateString = re.sub(r'\b([a-zA-Z_]\w*(\$\{[a-zA-Z0-9_.]+\})?\w*)(?=\[\$(\{index\}|index)\])',
                               r'_DBL(\1)',
                               templateString)
    
    dict['templateString'] = newTemplateString
  
  def loopOverVectorsWithInnerContentTemplateBegin(self, dict):
    if 'UNVECTORISABLE' in dict['originalTemplateString']:
      return
    else:
      return '#pragma ivdep\n'
  
