#!/usr/bin/env python
# encoding: utf-8
"""
XMDSScriptLexer.py

Created by Graham Dennis on 2008-11-18.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
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
  aliases = ['xmds', 'xpdeint']
  filenames = ['*.xmds']
  
  cdataRule = (r'(\<\!\[CDATA\[)(.*?)(\]\]\>)',
               bygroups(Comment.Preproc, using(XMDSCodeLexer), Comment.Preproc))
  
  tokens = XmlLexer.tokens.copy()
  tokens['root'].insert(0, cdataRule)
  
  def analyse_text(text):
    if XmlLexer.analyse_text(text) > 0 and '<simulation' in text:
      return 0.8
  

