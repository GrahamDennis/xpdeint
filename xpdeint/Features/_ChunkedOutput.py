#!/usr/bin/env python
# encoding: utf-8
"""
_ChunkedOutput.py

Created by Graham Dennis on 2010-09-17.

Copyright (c) 2010-2012, Graham Dennis

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

from xpdeint.ParserException import ParserException

class _ChunkedOutput (_Feature):
  def __init__(self, *args, **KWs):
    localKWs = self.extractLocalKWs(['chunkSize'], KWs)
    
    _Feature.__init__(self, *args, **KWs)
    
    self.chunkSize = localKWs['chunkSize']
  
  def preflight(self):
    super(_ChunkedOutput, self).preflight()
    
    for mg in self.getVar('momentGroups'):
      mg.propDimRep.setHasLocalOffset()
    
    outputFormat = self.getVar('features')['Output'].outputFormat
    if not outputFormat.mpiSafe:
      # If an output format is not mpi safe, then it isn't safe for us either
      # This is because MPI requires random access to the output file, just as we do.
      raise ParserException(
        self.xmlElement,
        "The 'chunked_output' feature cannot be used with the '%s' output format." % outputFormat.name
      )
    
    # We also can't work if something like the 'error_check' feature is used because it wants to use all the output data
    # at the end of the simulation
    for momentGroup in self.getVar('momentGroups'):
      if momentGroup.processedVector.aliases:
        # Anything that sets an alias is bad.  But that's not a helpful error message to provide to the user
        # So let's try and interpret why there are aliases on the processed vector
        for alias in momentGroup.processedVector.aliases:
          if alias.endswith('_halfstep'):
            error = "the 'error_check' feature.  They are mutually exclusive."
          elif alias.endswith('_sd'):
            error = "any of the 'multi-path' drivers.  They are mutually exclusive."
          else:
            # If this error is hit, it means that a new feature was added that collides with chunked_output, but
            # it didn't exist at the time that the chunked_output feature was created.  Please add a check here
            # for this new feature so that the user recieves a nicer error message.
            error = "any function of xmds2 that creates aliases of moment group processed vectors. "\
                    "Please send your script and report this error to %s" % self.getVar('bugReportAddress')
          raise ParserException(
            self.xmlElement,
            "The 'chunked_output' feature cannot be used with " + error
            )
  

