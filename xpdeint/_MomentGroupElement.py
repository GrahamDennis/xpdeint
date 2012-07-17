#!/usr/bin/env python
# encoding: utf-8
"""
_MomentGroupElement.py

This contains all the pure-python code for MomentGroupElement.tmpl

Created by Graham Dennis on 2007-10-18.

Copyright (c) 2007-2012, Graham Dennis

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

from xpdeint.ScriptElement import ScriptElement
from xpdeint.ParserException import ParserException

from xpdeint.Function import Function
from xpdeint.Utilities import lazy_property

class _MomentGroupElement (ScriptElement):
  def __init__(self, number, *args, **KWs):
    self.number = number
    self.name = 'mg' + str(self.number)
    
    ScriptElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.requiresInitialSample = False
    self.getVar('momentGroups').append(self)
    self.computedVectors = set()
    self.operatorContainers = []
    
    sampleFunctionName = ''.join(['_', self.id, '_sample'])
    sampleFunction = Function(name = sampleFunctionName,
                              args = [],
                              implementation = self.sampleFunctionContents)
    self.functions['sample'] = sampleFunction
    
    processFunctionName = ''.join(['_', self.id, '_process'])
    processFunction = Function(name = processFunctionName,
                               args = [],
                               implementation = self.processFunctionContents)
    self.functions['process'] = processFunction
    
    writeOutFunctionName = ''.join(['_', self.id, '_write_out'])
    writeOutFunction = Function(name = writeOutFunctionName,
                                args = [('FILE*', '_outfile')],
                                implementation = self.writeOutFunctionContents)
    self.functions['writeOut'] = writeOutFunction
  
  @property
  def children(self):
    children = super(_MomentGroupElement, self).children
    children.extend(self.computedVectors)
    children.extend(self.operatorContainers)
    return children
  
  @lazy_property
  def propDimRep(self):
    return self.outputField.dimensionWithName(self.propagationDimension).inBasis(self.outputBasis)
  
  # Do we actually need to allocate the moment group vector?
  # We may not need to allocate the raw vector if there is no
  # processing of the raw vector to be done before it is written.
  @lazy_property
  def rawVectorNeedsToBeAllocated(self):
    # If we have processing code, then we definitely need a raw vector
    if self.hasattr('processingCode') and self.processingCode: return True
    
    dict = {'returnValue': False, 'MomentGroup': self}
    featureOrdering = ['Driver']
    
    # This function allows the features to determine whether or not the raw vector
    # needs to be allocated by changing the value of the 'returnValue' key in dict.
    # The features should only change the value to true if they need the raw vector
    # allocated. Otherwise, they shouldn't touch the value.
    self.insertCodeForFeatures('rawVectorNeedsToBeAllocated', featureOrdering, dict)
    
    return dict['returnValue']
  
  def bindNamedVectors(self):
    super(_MomentGroupElement, self).bindNamedVectors()
    
    if not self.rawVectorNeedsToBeAllocated:
      self.outputField.managedVectors.remove(self.processedVector)
      self.processedVector.remove()
      self.processedVector = self.rawVector
    
  
  def addSamplePoints(self, samplePoints):
    self.outputField.dimensionWithName(self.propagationDimension).inBasis(self.outputBasis).runtimeLattice += samplePoints
  
  def preflight(self):
    super(_MomentGroupElement, self).preflight()
    for dependency in self.codeBlocks['sampling'].dependencies:
      if self.hasPostProcessing and dependency.type == 'complex':
        self.rawVector.type = 'complex'
    
    # Throw out the propagation dimension if it only contains a single sample
    if self.outputField.hasDimensionName(self.propagationDimension):
      propDimRep = self.propDimRep
      if propDimRep.runtimeLattice == 1:
        self.propDimRep = None
        singlePointDimension = self.outputField.dimensionWithName(self.propagationDimension)
        self.outputField.dimensions.remove(singlePointDimension)
        singlePointDimension.remove()
        self.outputBasis = tuple(b for b in self.outputBasis if not b is propDimRep.canonicalName)
        for vector in self.outputField.vectors:
          basesNeeded = set(tuple(b for b in basis if not b is propDimRep.canonicalName) for basis in vector.basesNeeded)
          vector.basesNeeded.clear()
          vector.basesNeeded.update(basesNeeded)
          vector.field._basisForBasisCache.clear()
          vector.initialBasis = tuple(b for b in vector.initialBasis if not b is propDimRep.canonicalName)
    
    geometry = self.getVar('geometry')
    singlePointSamplingDims = [dim.name for dim in geometry.dimensions \
        if any(dimRep.canonicalName in self.singlePointSamplingBasis for dimRep in dim.representations)]
    
    loopingDimensionNames = set([dim.name for dim in self.samplingField.dimensions]).union(singlePointSamplingDims)
    for dependency in self.codeBlocks['sampling'].dependencies:
      missingLoopingDimensionNames = set(dim.name for dim in dependency.field.dimensions).difference(loopingDimensionNames)
      if missingLoopingDimensionNames:
        raise ParserException(self.codeBlocks['sampling'].xmlElement,
                    "The dimension(s) %s have not been included in the basis specification.  "
                    "They are needed by the vector '%s'." % (', '.join(missingLoopingDimensionNames), dependency.name))
    
    self.codeBlocks['sampling'].basis = (self.propagationDimension,) \
                                      + self.codeBlocks['sampling'].basis \
                                      + self.singlePointSamplingBasis
    
    outputFieldID = self.outputField.id
    propagationDimension = self.propagationDimension
    self.codeBlocks['sampling'].loopArguments['indexOverrides'] = \
      {propagationDimension: {self.outputField: "_%(outputFieldID)s_index_%(propagationDimension)s" % locals()}}
    
    self.integratingComponents = bool(loopingDimensionNames.difference(set([dim.name for dim in self.outputField.dimensions])))
    if self.integratingComponents:
      # We are integrating over dimensions, and therefore the rawVector is an index override
      self.codeBlocks['sampling'].loopArguments['vectorOverrides'] = [self.rawVector]
    
  
  


