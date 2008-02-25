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

import re
import RegularExpressionStrings

class _ScriptElement (Template):
  # Initialise the callOnceGuards to be empty
  _callOncePerClassGuards = set()
  _callOncePerInstanceGuards = dict()
  
  @classmethod
  def resetGuards(cls):
    _ScriptElement._callOncePerClassGuards.clear()
    for instanceGuardSet in _ScriptElement._callOncePerInstanceGuards.itervalues():
      instanceGuardSet.clear()
  
  def __init__(self, *args, **KWs):
    Template.__init__(self, *args, **KWs)
    
    self.getVar('templates').add(self)
    
    self.filterTemplateArgument = KWs['filter']
    self.searchListTemplateArgument = KWs['searchList']
    self.dependencies = set()
    
    if self.hasattr('globalNameSpaceName'):
      globalNameSpace = KWs['searchList'][0]
      globalNameSpace[self.globalNameSpaceName] = self
      if not self in globalNameSpace['scriptElements']:
        globalNameSpace['scriptElements'].append(self)
    
    # Create the entry in the callOnceGuards
    _ScriptElement._callOncePerInstanceGuards[self] = set()
    
  
  def hasattr(self, attrName):
    try:
      getattr(self, attrName)
    except AttributeError, err:
      if hasattr(type(self), attrName):
        raise
      return False
    else:
      return True
  
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
  
  # Define a whole bunch of static versions of these functions
  def static_includes(self):
    pass
  
  def static_defines(self):
    pass
  
  def static_globals(self):
    pass
  
  def static_functionPrototypes(self):
    pass
  
  def static_functionImplementations(self):
    pass
  
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
      if not feature.hasattr(functionName):
        continue
      
      # Get functionName on feature by name
      featureFunction = getattr(feature, functionName)
      
      # Get the extra indent value, if we were passed one in the dict object
      extraIndent = dict.get('extraIndent', 0)
      
      # The caller object is self.
      dict['caller'] = self
      
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
      return 'k' + dimension.name
    else:
      return dimension.name
  
  # Insert contents of function for children
  def implementationsForChildren(self, functionName, *args, **KWs):
    if not self.hasattr('children'):
      return
    result = []
    blankLineSeparator = ''
    for child in self.children:
      if child.hasattr(functionName) and callable(getattr(child, functionName)):
        childFunction = getattr(child, functionName)
        childFunctionOutput = childFunction(*args, **KWs)
        if childFunctionOutput and not childFunctionOutput.isspace():
          result.append(blankLineSeparator)
          blankLineSeparator = '\n'
          result.append(childFunctionOutput)
    
    return ''.join(result)
  
  def implementationsForClassesAndChildren(self, functionName, *args, **KWs):
    result = []
    blankLineSeparator = ''
    staticFunctionName = 'static_' + functionName
    if self.hasattr('static_' + functionName):
      staticFunction = getattr(self, staticFunctionName)
      staticFunctionOutput = staticFunction(*args, **KWs)
      if staticFunctionOutput and not staticFunctionOutput.isspace():
        blankLineSeparator = '\n'
        result.append(staticFunctionOutput)
    childOutput = self.implementationsForChildren(functionName, *args, **KWs)
    if childOutput:
      result.append(blankLineSeparator)
      result.append(childOutput)
    
    return ''.join(result)
  
  def createNamedVectors(self):
    pass
  
  def bindNamedVectors(self):
    pass
  
  def preflight(self):
    pass
  
  def vectorsFromEntity(self, entity):
    vectors = set()
    vectorDictionary = dict([(vector.name, vector) for vector in self.getVar('vectors')])
    for vectorName in entity.value:
      if not vectorName in vectorDictionary:
        raise ParserException(entity.xmlElement, "Unknown vector '%(vectorName)s'." % locals())
      vectors.add(vectorDictionary[vectorName])
    return vectors
 
    
  def transformVectorsToSpace(self, vectors, space):
     '''Transform vectors $vectors to space $space.'''
     result=""
     for vector in vectors:
         if not (vector.initialSpace) == (space & vector.field.spaceMask):
           if not vector.type == "complex":
             raise ParserException(self.xmlElement,
                     "Cannot satisfy dependence on vector '%s' because it is not "
                     "of type complex, and needs to be fourier transformed during sampling." % vector.name)
         if vector.needsFourierTransforms:
           result+="_"+vector.id+"_go_space("+str(space)+");\n"
         # Add space $space to the set of spaces in which this vector is needed
         vector.spacesNeeded.add(space & vector.field.spaceMask) 
     return result
    
  
  def remove(self):
    self.getVar('templates').discard(self)
    scriptElements = self.getVar('scriptElements')
    
    for someIterable in (self.getVar('scriptElements'), self.getVar('fields'),
                         self.getVar('vectors'), self.getVar('momentGroups')):
      while self in someIterable:
        someIterable.remove(self)
    
  
  def fixupComponentsWithIntegerValuedDimensions(self, vectors, code):
    if self.getVar('geometry').integerValuedDimensions:
      components = set()
      
      for vector in vectors:
        components.update(vector.components)
      
      componentsWithIntegerValuedDimensionsRegex = \
        re.compile(RegularExpressionStrings.componentWithIntegerValuedDimensions(components),
                   re.VERBOSE)
      
      originalCode = code
      
      for match in componentsWithIntegerValuedDimensionsRegex.finditer(originalCode):
        # So we now have a component, but if it doesn't have a match for 'integerValuedDimensions'
        # then we don't have to do anything with it.
        if not match.group('integerValuedDimensions'):
          continue
        
        componentName = match.group('componentName')
        tempVectors = [v for v in vectors if componentName in v.components]
        assert len(tempVectors) == 1
        
        vector = tempVectors[0]
        regex = re.compile(RegularExpressionStrings.componentWithIntegerValuedDimensionsWithComponentAndField(componentName, vector.field),
                           re.VERBOSE)
        
        integerValuedDimensionsMatch = regex.search(code)
        
        if not integerValuedDimensionsMatch:
          target = match.group(0)
          raise ParserException(self.xmlElement,
                                "Unable to extract the integer-valued dimensions for the '%(componentName)s' variable.\n"
                                "The string that couldn't be parsed was '%(target)s'." % locals())
        
        integerValuedDimensions = vector.field.integerValuedDimensions
        
        integerValuedDimensionNames = []
        for dimList in integerValuedDimensions:
          integerValuedDimensionNames.extend([dim.name for dim in dimList])
        
        # We can do an optimisation here, components accessed with the 'normal' pattern
        # can be stripped of the integer-valued dimension specifiers. i.e.
        # phi[j, k] can become just 'phi' if the first integer-valued dimension is 'j' and
        # the second is 'k'.
        
        canOptimiseIntegerValuedDimensions = all([integerValuedDimensionsMatch.group(dimName).strip() == dimName for dimName in integerValuedDimensionNames])
        
        if canOptimiseIntegerValuedDimensions:
          replacementString = componentName
        else:
          argumentsString = ', '.join([integerValuedDimensionsMatch.group(dimName).strip() for dimName in integerValuedDimensionNames])
          
          replacementString = '_%(componentName)s(%(argumentsString)s)' % locals()
        
        escape = RegularExpressionStrings.escapeStringForRegularExpression
        
        # Create a regular expression to replace the phi[j] string with the appropriate string
        operatorCodeReplacementRegex = re.compile(r'\b' + escape(componentName) + escape(match.group('integerValuedDimensions')))
        
        code = operatorCodeReplacementRegex.sub(replacementString, code, count = 1)
    
    return code
  
