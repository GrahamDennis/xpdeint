#!/usr/bin/env python
# encoding: utf-8
"""
_ScriptElement.py

This contains all the pure-python code for ScriptElement.tmpl

Created by Graham Dennis on 2007-10-17.
Copyright (c) 2007 __MyCompanyName__. All rights reserved.
"""

import sys

from Cheetah.Template import Template
from IndentFilter import IndentFilter
from ParserException import ParserException

class _ScriptElement (Template):
  def __init__(self, *args, **KWs):
    Template.__init__(self, *args, **KWs)
    
    objectMap = self.getVar('objectMap')
    
    if not self.__class__ in objectMap:
      objectMap[self.__class__] = set()
    
    objectMap[self.__class__].add(self)
  
  # Default description of the template
  def description(self):
    return type(self).__name__
  
  # Includes
  def includes(self):
    return self.implementationsForClassesAndChildren('includes')
  
  # Defines needed at the start of the simulation
  def defines(self):
    return self.implementationsForClassesAndChildren('defines')
  
  # Globals needed at the start of the simulation
  def globals(self):
    return self.implementationsForClassesAndChildren('globals')
  
  # Function prototypes
  def functionPrototypes(self):
    return self.implementationsForClassesAndChildren('functionPrototypes')
  
  # Function implemenations
  def functionImplementations(self):
    return self.implementationsForClassesAndChildren('functionImplementations')
  
  # Insert code for a list of features by calling a named function
  def insertCodeForFeatures(self, functionName, featureList, dict = {}, reverse = False):
    featureDictionary = self.getVar('features')
    
    result = []
    indentFilter = IndentFilter()
    
    # Loop over the features that we should include
    for featureName in featureList:
      if not featureDictionary.has_key(featureName):
        # If we don't have the feature, then there isn't much we can do
        continue
      
      # Grab the feature
      feature = featureDictionary[featureName]
      
      # If the function doesn't exist, we're done
      if not hasattr(feature, functionName):
        continue
      
      # Get functionName on feature by name
      featureFunction = getattr(feature, functionName)
      
      # Get the extra indent value, if we were passed one in the dict object
      extraIndent = dict.get('extraIndent', 0)
      
      # Get the caller object from the previous frame
      callerFrame = sys._getframe(1)
      dict['caller'] = callerFrame.f_locals['self']
      del callerFrame
      
      # Call the function with optional dictionary
      featureResult = featureFunction(dict)
      
      if not reverse:
        # If we're doing this in the forward order, then we use the initial indent as the indent for the result
        result.append(indentFilter.filter(featureResult, extraIndent=extraIndent))
      else:
        # If we're doing this in reverse order, then we use the final indent as the indent for the result
        result.append(indentFilter.filter(featureResult, extraIndent=dict.get('extraIndent', 0)))
    
    return ''.join(result)
  
  # Insert code for a list of features (in reverse order) by calling a named function
  def insertCodeForFeaturesInReverseOrder(self, functionName, featureList, dict = {}):
    # Create a reversed feature list
    reversedFeatureList = featureList[:]
    reversedFeatureList.reverse()
    
    return self.insertCodeForFeatures(functionName, reversedFeatureList, dict, reverse=True)
  
  # Is the dimension in fourier space?
  def dimensionIsInFourierSpace(self, dimension, space):
    geometryDimensionNumber = self.getVar('geometry').indexOfDimension(dimension)
    if space & (1 << geometryDimensionNumber):
      # This dimension is in fourier space
      return True
    else:
      # This dimension isn't in fourier space
      return False
  
  # Return the name of the dimension considering the current space
  def dimensionNameForSpace(self, dimension, space):
    if self.dimensionIsInFourierSpace(dimension, space):
      return 'k' + dimension['name']
    else:
      return dimension['name']
  
  # Insert contents of function for children
  def implementationsForChildren(self, functionName, arguments=[]):
    if not hasattr(self, 'children'):
      return
    result = []
    blankLineSeparator = ''
    for child in self.children:
      if hasattr(child, functionName) and callable(getattr(child, functionName)):
        childFunction = getattr(child, functionName)
        childFunctionOutput = childFunction(*arguments)
        if childFunctionOutput:
          result.append(blankLineSeparator)
          blankLineSeparator = '\n'
          result.append(childFunctionOutput)
    
    return ''.join(result)
  
  def implementationsForClassesAndChildren(self, functionName, arguments=[]):
    result = []
    blankLineSeparator = ''
    staticFunctionName = 'static_' + functionName
    if hasattr(self, 'static_' + functionName):
      staticFunction = getattr(self, staticFunctionName)
      staticFunctionOutput = staticFunction(*arguments)
      if staticFunctionOutput:
        blankLineSeparator = '\n'
        result.append(staticFunctionOutput)
    childOutput = self.implementationsForChildren(functionName, arguments)
    if childOutput:
      result.append(blankLineSeparator)
      result.append(childOutput)
    
    return ''.join(result)
  
  def preflight(self):
    if hasattr(self, 'children'):
      for child in self.children:
        child.preflight()
  
  def vectorsFromEntity(self, entity):
    vectors = set()
    vectorDictionary = dict([(vector.name, vector) for vector in self.getVar('vectors')])
    for vectorName in entity.value:
      if not vectorName in vectorDictionary:
        raise ParserException(entity.xmlElement, "Unknown vector '%(vectorName)s'." % locals())
      vectors.add(vectorDictionary[vectorName])
    return vectors
