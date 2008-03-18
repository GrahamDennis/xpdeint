#!/usr/bin/env python
# encoding: utf-8
"""
_MomentGroupElement.py

This contains all the pure-python code for MomentGroupElement.tmpl

Created by Graham Dennis on 2007-10-18.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

from FieldElement import FieldElement
from ParserException import ParserException

class _MomentGroupElement (FieldElement):
  def __init__(self, number, *args, **KWs):
    self.number = number
    
    FieldElement.__init__(self, *args, **KWs)
    
    # Set default variables
    self.requiresInitialSample = False
    self.getVar('momentGroups').append(self)
    self.computedVectors = set()
    self.operatorContainers = []
  
  @property
  def children(self):
    result = set(super(_MomentGroupElement, self).children)
    result.update(self.computedVectors)
    result.update(self.operatorContainers)
    return result
  
  # The name of the moment group (used for the vector names, etc)
  @property
  def name(self):
    return 'mg' + str(self.number)
  
  # Do we actually need to allocate the moment group vector?
  # We may not need to allocate the raw vector if there is no
  # processing of the raw vector to be done before it is written.
  @property
  def rawVectorNeedsToBeAllocated(self):
    # If we have processing code, then we definitely need a raw vector
    if self.hasattr('processingCode') and self.processingCode:
      return True
    
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
    
    dependencies = self.vectorsFromEntity(self.dependenciesEntity)
    
    if self.hasattr('sampleField'):
      sampleSpaceMask = self.sampleField.spaceMask
    else:
      sampleSpaceMask = self.spaceMask
    
    for dependency in dependencies:
      if self.hasPostProcessing and dependency.type == 'complex':
        self.rawVector.type = 'complex'
      
    
    self.dependencies.update(dependencies)
  


