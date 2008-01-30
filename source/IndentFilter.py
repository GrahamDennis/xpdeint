#!/usr/bin/env python
# encoding: utf-8
"""
IndentFilter.py

Created by Graham Dennis on 2007-08-29.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from Cheetah.Filters import Filter

import sys

## This is oh-so-hackish. I say this because 'trans' is a transaction
## that is designed to be used when Cheetah is used in WebWare
## servlets. Fortunately for me, a dummy transaction is always
## available that buffers output for every function, so I can just
## ask the transaction for the buffer, and extract the last line to get
## the context for this replacement. If it is pure whitespace, then I
## know that each line of the replacement text (except the first)
## should begin with that whitespace. The first line doesn't need the
## whitespace because it was there before the call.
##
## The result of all this is that if you want auto-indentation, you just
## need to call the filter with the argument autoIndent=True. The following is
## an example of typical usage:
##     ${someRandomVariableOrFunction, autoIndent=True}#slurp
## This way, the four characters of whitespace before the variable replacement
## will be used for each line of the replacement text.
##
## The transaction is obtained from the calling frame using Python's introspection
## capabilities. (Go Python!)
##
## Additionally, the option 'extraIndent=n' can be passed which increases
## the indent by n spaces.

class IndentFilter(Filter):
  def filter(self, val, **kw):
    ## Quickly check for the case where we have nothing to do
    if not (kw.get('autoIndent') or kw.get('extraIndent')):
      return super(IndentFilter, self).filter(val, **kw)
    trans = None
    indentString = ''
    firstLineIndent = ''
    ## Add the extra indent spaces
    if kw.get('extraIndent'):
      indentString += ' '*kw['extraIndent']
      firstLineIndent += ' '*kw['extraIndent']
    if kw.get('autoIndent'):
      if not trans:
        ## Grab the transaction object from our caller's frame. Yay introspection.
        callerFrame = sys._getframe(1)
        trans = callerFrame.f_locals['trans']
        del callerFrame
      lastLine = trans.response().getvalue().rpartition('\n')[2]
      ## only add the contents of the last line if it consists of only whitespace
      if lastLine.isspace():
        indentString += lastLine
    replacementString = super(IndentFilter, self).filter(val, **kw)
    ## If we were supposed to be indenting and we have no replacement, then we need to clear
    ## up that indent, but only if we are auto-indenting
    if kw.get('autoIndent') and len(replacementString) == 0:
      if not trans:
        callerFrame = sys._getframe(1)
        trans = callerFrame.f_locals['trans']
        del callerFrame
      (everythingBeforeLastLine, sep, lastLine) = trans.response().getvalue().rpartition('\n')
      ## only erase the last line if it is only whitespace
      if lastLine.isspace():
        del trans.response()._outputChunks[:]
        trans.response()._outputChunks.append(everythingBeforeLastLine + "\n")
    ## if either the indent string or the replacement string is empty, there's nothing to do
    if len(indentString) == 0 or len(replacementString) == 0:          
      return replacementString
    ## split the replacement string into lines (keeping the newline characters)
    replacementLines = replacementString.splitlines(True)
    ## we don't do anything to the first line (except add the firstLineIndent),
    ## so if there's only one, we're pretty much done
    if len(replacementLines) == 1:
      return firstLineIndent + replacementString
    ## add the firstLineIndent to the first line.
    if len(firstLineIndent):
      replacementLines[0] = firstLineIndent + replacementLines[0]
    ## add the indentString to the start of each line (except the first). (Yay Python)
    replacementLines[1:] = map(lambda x: indentString + x, replacementLines[1:])
    return "".join(replacementLines)
