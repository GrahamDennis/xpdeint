#!/usr/bin/env python
# encoding: utf-8
"""
AutoVectorise.py

Created by Graham Dennis on 2008-02-07.

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

from xpdeint.Features._Feature import _Feature

import re

class _AutoVectorise (_Feature):
  
  # Match things of the form someSymbol${someSubstitution}restOfSymbol[${index}]
  # where the ${someSubstitution} is optional, and the curly braces around the
  # index replacement are also optional.
  arrayNameRegex = re.compile(r'\b([a-zA-Z_]\w*(?:\$\{[a-zA-Z0-9_.]+\}\w*)?)(?=\[\$(?:\{index\}|index)\])')
  
  def loopOverVectorsWithInnerContentTemplateModifyTemplate(self, dict):
    """
    Modifies the ``templateString`` to add in auto-vectorisation features.
    
    This function is called from `ScriptElement`'s `loopOverVectorsWithInnerContentTemplate`.
    """
    templateString = dict['templateString']
    
    if 'UNVECTORISABLE' in templateString:
      dict['vectorisable'] = False
      return
    else:
      dict['vectorisable'] = True
    
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
    
    arrayNames = set(self.arrayNameRegex.findall(templateString))
    
    # Create a template prefix that creates the *_dbl variables
    vectorisationPreambleContents = ''.join(['  _MAKE_AUTOVEC_VARIABLE(%s);\n' % arrayName for arrayName in arrayNames])
    
    vectorisationPreambleTemplateFunction = ''.join(["@def vectorisationPreamble\n",
                                                     vectorisationPreambleContents,
                                                     "@end def\n"])
    
    newTemplateString = self.arrayNameRegex.sub(r'_AUTOVEC(\1)', templateString)
    
    dict['templateString'] = newTemplateString
    dict['templateFunctions'].append(vectorisationPreambleTemplateFunction)
  
  def loopOverVectorsWithInnerContentTemplateBegin(self, dict):
      if not dict['vectorisable']:
        return '#pragma novector\n'
      else:
        dblVariableConstruction = dict['template'].vectorisationPreamble()
        dict['extraIndent'] += 2
        return ''.join(['{\n',
                        dblVariableConstruction,
                        '  #pragma ivdep\n'])
  
  def loopOverVectorsWithInnerContentTemplateEnd(self, dict):
    if not dict['vectorisable']:
      return
    else:
      dict['extraIndent'] -= 2
      return '}\n'
  
