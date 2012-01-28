#!/usr/bin/env python
# encoding: utf-8
"""
XMDSScriptLexer.py

Created by Graham Dennis on 2008-11-18.

Copyright (c) 2008-2012, Graham Dennis

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of The Australian National University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

from pygments.lexers.web import XmlLexer
from pygments.lexers.compiled import CLexer
from pygments.lexer import bygroups, using
from pygments.token import Comment, Keyword, Name

class XMDSCodeLexer(CLexer):
  """
  A lexer for the code sections of XMDS/xpdeint simulation scripts.
  
  Only to be used by the XMDSScriptLexer.
  """
  
  name = 'XMDS-Code'
  aliases = ['xmds-code', 'xpdeint-code']
  filenames = []
  
  xmds_types = set(['complex', 'fftw_complex'])
  xmds_functions = set(['rcomplex', 'pcomplex', 'real', 'imag', 'mod', 'mod2',
                        'arg', 'conj', 'c_exp', 'c_log', 'c_sqrt'])
  xmds_constants = set(['i'])
  
  def get_tokens_unprocessed(self, text):
    for index, token, value in CLexer.get_tokens_unprocessed(self, text):
      if token is Name:
        if value in self.xmds_types:
          token = Keyword.Type
        elif value in self.xmds_functions:
          token = Name.Function
        elif value in self.xmds_constants:
          token = Keyword.Constant
      yield index, token, value
      
  

class XMDSScriptLexer(XmlLexer):
  """
  A lexer for XMDS/xpdeint simulation scripts.
  """
  
  
  name = 'XMDS'
  aliases = ['xmds2','xmds','xpdeint']
  filenames = ['*.xmds']
  
  cdataRule = (r'(\<\!\[CDATA\[)(.*?)(\]\]\>)',
               bygroups(Comment.Preproc, using(XMDSCodeLexer), Comment.Preproc))
  
  tokens = XmlLexer.tokens.copy()
  tokens['root'].insert(0, cdataRule)
  
  def analyse_text(text):
    if XmlLexer.analyse_text(text) > 0 and '<simulation' in text:
      return 0.8
  

