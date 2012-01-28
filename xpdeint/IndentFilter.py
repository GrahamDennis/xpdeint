#!/usr/bin/env python
# encoding: utf-8
"""
IndentFilter.py

Created by Graham Dennis on 2007-08-29.

Copyright (c) 2007-2012, Graham Dennis

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of The Australian National University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

from Cheetah.Filters import Filter

import sys

class IndentFilter(Filter):
  def filter(self, val, **kw):
    """
    Cheetah filter for indenting code.
    
    This is oh-so-hackish. I say this because ``trans`` is a transaction
    that is designed to be used when Cheetah is used in WebWare
    servlets. Fortunately for me, a dummy transaction is always
    available that buffers output for every function, so I can just
    ask the transaction for the buffer, and extract the last line to get
    the context for this replacement. If it is pure whitespace, then I
    know that each line of the replacement text (except the first)
    should begin with that whitespace. The first line doesn't need the
    whitespace because it was there before the call.
    
    The result of all this is that if you want auto-indentation, you just
    need to call the filter with the argument ``autoIndent=True``. The following is
    an example of typical usage::
    
        <some whitespace>${someRandomVariableOrFunction, autoIndent=True}@slurp
    
    This way, the whitespace before the variable replacement will be used for each
    line of the replacement text.
    
    The transaction is obtained from the calling frame using Python's introspection
    capabilities. (Go Python!)
    
    Additionally, the option ``extraIndent=n`` can be passed which increases
    the indent by ``n`` spaces.
    """
    # Quickly check for the case where we have nothing to do
    if not (kw.get('autoIndent') or kw.get('extraIndent')):
      return super(IndentFilter, self).filter(val, **kw)
    trans = None
    indentString = ''
    firstLineIndent = ''
    # Add the extra indent spaces
    if kw.get('extraIndent'):
      indentString += ' '*kw['extraIndent']
      firstLineIndent += ' '*kw['extraIndent']
    
    replacementString = super(IndentFilter, self).filter(val, **kw)
    
    # If the replacement string is just space, just use an empty string instead.
    if replacementString == None or replacementString.isspace():
      replacementString = ''
    
    if kw.get('autoIndent'):
      # Grab the transaction object from our caller's frame. Yay introspection.
      callerFrame = sys._getframe(1)
      trans = callerFrame.f_locals['trans']
      del callerFrame
      
      temp = trans.response().getvalue().rsplit('\n', 1)
      everythingBeforeLastLine = temp[0]
      lastLine = temp[-1]
      
      # Only add the contents of the last line to the indent string if it is only whitespace
      if lastLine.isspace():
        indentString += lastLine
      
      # Erase the last line and return an empty string if we have no replacement
      # But only if the last line consists of pure whitespace
      if len(replacementString) == 0 and lastLine.isspace():
        del trans.response()._outputChunks[:]
        trans.response()._outputChunks.append(everythingBeforeLastLine + '\n')
        return ''
    
    # if either the indent string or the replacement string is empty, there's nothing to do
    if len(indentString) == 0 or len(replacementString) == 0:
      return replacementString
    
    # split the replacement string into lines (keeping the newline characters)
    replacementLines = replacementString.splitlines(True)
    
    # we don't do anything to the first line (except add the firstLineIndent),
    # so if there's only one, we're pretty much done
    if len(replacementLines) == 1:
      return firstLineIndent + replacementString
    
    # add the firstLineIndent to the first line.
    if len(firstLineIndent):
      replacementLines[0] = firstLineIndent + replacementLines[0]
    
    # add the indentString to the start of each line (except the first). (Yay Python)
    replacementLines[1:] = map(lambda x: indentString + x, replacementLines[1:])
    return "".join(replacementLines)
  
