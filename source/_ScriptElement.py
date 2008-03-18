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
  argumentsToTemplateConstructors = {}
  # Initialise the callOnceGuards to be empty
  _callOnceGuards = set()
  _callOncePerInstanceGuards = dict()
  
  @classmethod
  def resetGuards(cls):
    _ScriptElement._callOnceGuards.clear()
    for instanceGuardSet in _ScriptElement._callOncePerInstanceGuards.itervalues():
      instanceGuardSet.clear()
  
  _ScriptElement_haveCalledInit = False
  
  def __init__(self, *args, **KWs):
    # If we have a diamond-inheritence, this function could be called more than once
    # And that would be bad. Let's check for that case, and return if it is the case.
    # Template can deal with being called more than once, but some of the code below
    # wouldn't be safe called more than once
    if self._ScriptElement_haveCalledInit:
      return
    
    self._ScriptElement_haveCalledInit = True
    
    legalKWs = ['xmlElement']
    localKWs = {}
    for key in KWs.copy():
      if key in legalKWs:
        localKWs[key] = KWs[key]
        del KWs[key]
    
    Template.__init__(self, *args, **KWs)
    
    self.getVar('templates').add(self)
    
    # Only set the dependencies attribute if it isn't taken
    # care of elsewhere
    if not hasattr(type(self), 'dependencies'):
      self.dependencies = set()
    
    self._parent = None
    self._propagationDimension = None
    self._propagationDirection = None
    self.xmlElement = localKWs.get('xmlElement', None)
    
    if self.hasattr('globalNameSpaceName'):
      globalNameSpace = KWs['searchList'][0]
      globalNameSpace[self.globalNameSpaceName] = self
      if not self in globalNameSpace['scriptElements']:
        globalNameSpace['scriptElements'].append(self)
    
    # Create the entry in the callOnceGuards
    _ScriptElement._callOncePerInstanceGuards[self] = set()
    
  
  @property
  def parent(self):
    if self._parent:
      return self._parent
    
    potentialParents = filter(lambda x: x.hasattr('children') and self in x.children, self.getVar('templates'))
    
    if not potentialParents:
      return None
    
    if len(potentialParents) > 1:
      raise AssertionError("We seem to have more than one parent: " + ', '.join([repr(potentialParent) for potentialParent in potentialParents]))
    
    self._parent = potentialParents[0]
    return self._parent
  
  @property
  def id(self):
    result = []
    currentObject = self
    while currentObject:
      if currentObject.hasattr('name') and currentObject.name:
        result.append(currentObject.name)
      currentObject = currentObject.parent
    result.reverse()
    return '_'.join(result)
  
  def _getPropagationDimension(self):
    if self._propagationDimension:
      return self._propagationDimension
    
    if self.parent:
      return self.parent.propagationDimension
    
    return self.getVar("globalPropagationDimension")
  
  def _setPropagationDimension(self, value):
    self._propagationDimension = value
  
  propagationDimension = property(_getPropagationDimension, _setPropagationDimension)
  del _getPropagationDimension, _setPropagationDimension
  
  def _getPropagationDirection(self):
    if self._propagationDirection:
      return self._propagationDirection
    
    if self.parent:
      return self.parent.propagationDirection
    
    return '+'
  
  def _setPropagationDirection(self, value):
    self._propagationDirection = value
  
  propagationDirection = property(_getPropagationDirection, _setPropagationDirection)
  del _getPropagationDirection, _setPropagationDirection
  
  def hasattr(self, attrName):
    try:
      getattr(self, attrName)
    except AttributeError, err:
      if hasattr(type(self), attrName):
        raise
      return False
    else:
      return True
  
  def valueForKeyPath(self, keyPath):
    """Return the value for a dotted-name lookup of `keyPath` anchored at `self`."""
    attrNames = keyPath.split('.')
    try:
      currentObject = self
      for attrName in attrNames:
        currentObject = getattr(currentObject, attrName)
    except Exception, err:
      selfRep = repr(self)
      print >> sys.stderr, "Hit exception trying to get keyPath '%(keyPath)s' on object %(selfRep)s." % locals()
      raise
    return currentObject
  
  def setValueForKeyPath(self, value, keyPath):
    """Set the value of the result of the dotted-name lookup of `keyPath` anchored at `self` to `value`."""
    attrNames = keyPath.split('.')
    lastAttrName = attrNames.pop()
    currentObject = self
    try:
      for attrName in attrNames:
        currentObject = getattr(currentObject, attrName)
      setattr(currentObject, lastAttrName, value)
    except Exception, err:
      selfRep = repr(self)
      print >> sys.stderr, "Hit exception trying to set keyPath '%(keyPath)s' on object %(selfRep)s." % locals()
      raise
    
  
  # Default description of the template
  def description(self):
    return type(self).__name__
  
  # Includes
  def includes(self):
    pass
  
  # Defines needed at the start of the simulation
  def defines(self):
    pass
  
  # Globals needed at the start of the simulation
  def globals(self):
    pass
  
  # Function prototypes
  def functionPrototypes(self):
    pass
  
  # Function implemenations
  def functionImplementations(self):
    pass
  
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
  def insertCodeForFeatures(self, functionName, featureList, dict = None, reverse = False):
    featureDictionary = self.getVar('features')
    
    if not dict:
        dict = {}
    
    if self.hasattr('bannedFeatures') and self.bannedFeatures:
      # Check if any of the features in the featureList are in the bannedFeatures
      bannedFeatures = self.bannedFeatures
      featureList = filter(lambda x: x not in bannedFeatures, featureList)
    
    result = []
    indentFilter = IndentFilter()
    dict['featureList'] = featureList
    
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
  def insertCodeForFeaturesInReverseOrder(self, functionName, featureList, dict = None):
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
  
  # Insert contents of function for self, classes and children
  def implementationsForFunctionName(self, functionName, *args, **KWs):
    result = []
    blankLineSeparator = ''
    staticFunctionName = 'static_' + functionName
    
    for attrName in [staticFunctionName, functionName]:
      if self.hasattr(attrName):
        function = getattr(self, attrName)
        functionOutput = function(*args, **KWs)
        if functionOutput and not functionOutput.isspace():
          result.append(blankLineSeparator)
          blankLineSeparator = '\n'
          result.append(functionOutput)
    
    if self.hasattr('children'):
      for child in self.children:
        result.append(blankLineSeparator)
        blankLineSeparator = '\n'
        result.append(child.implementationsForFunctionName(functionName, *args, **KWs))
    
    return ''.join(result)
  
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
  
  def bindNamedVectors(self):
    pass
  
  def preflight(self):
    pass
  
  def vectorsFromEntity(self, entity):
    vectors = set()
    vectorDictionary = dict([(vector.name, vector) for vector in self.getVar('vectors')])
    
    ancestors = []
    currObject = self
    while currObject:
      ancestors.append(currObject)
      currObject = currObject.parent
    
    for vectorName in entity.value:
      if not vectorName in vectorDictionary:
        raise ParserException(entity.xmlElement, "Unknown vector '%(vectorName)s'." % locals())
      vector = vectorDictionary[vectorName]
      if not (vector.parent == vector.field or vector.parent in ancestors):
        raise ParserException(entity.xmlElement, "Cannot access vector '%(vectorName)s' here. It is not available in this scope." % locals())
      vectors.add(vector)
    return vectors
    
  
  def transformVectorsToSpace(self, vectors, space):
    """Transform vectors `vectors` to space `space`."""
    result = []
    for vector in vectors:
      if not (vector.initialSpace) == (space & vector.field.spaceMask):
        if not vector.type == "complex":
          raise ParserException(self.xmlElement,
                  "Cannot satisfy dependence on vector '%s' because it is not "
                  "of type complex, and needs to be fourier transformed." % vector.name)
      if vector.needsFourierTransforms:
        result.extend(['_', vector.id, '_go_space(', str(space), ');\n'])
      # Add space $space to the set of spaces in which this vector is needed
      vector.spacesNeeded.add(space & vector.field.spaceMask)
    return ''.join(result)
  
  
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
  
  def templateObjectFromStringWithTemplateVariables(self, templateString, templateVars):
    settings = {'directiveStartToken': '@',
                'commentStartToken': '@#',
                'multiLineCommentStartToken': '@*',
                'multiLineCommentEndToken': '*@'
               }
    return Template(source = templateString,
                    searchList = [templateVars],
                    compilerSettings = settings)
  
  
  def _computedVectorOrderingForVectors(self, vectors):
    """
    Return the ordering for the computed vectors in `vectors` taking into account
    any dependencies between the computed vectors.
    """
    
    stack = []
    
    # The algorithm here is basically to start with any given vector and traverse
    # the dependencies recursively until a vector with no dependencies is found,
    # then it is added to the list of ordered dependencies. If, during a traversal,
    # a vector is encountered twice (the history of traversed dependencies is stored
    # in the stack variable), then a circular dependency chain has been hit and a
    # ParserException will be raised. Once all of a vector's dependencies have been
    # added to the orderedDependencies, the vector itself can be added.
    # Finally, if a vector is already in orderedDependencies, we don't need to consider
    # its dependencies as they will have already been considered when considering the
    # dependencies of another vector that depends on the first vector. Clear as mud?
    
    def orderedDependenciesForVectors(vectors):
      """
      Helper function that is called recursively to return the ordering for the computed
      vectors such that all dependencies of a computed vector are evaluated first. Any
      circular dependencies will result in a ParserException.
      """
      orderedDependencies = []
      for v in vectors:
        # If v is in the ordering, then it has already been taken care of
        if v in orderedDependencies:
          continue
        
        # If v is on the stack, then we have a circular dependency
        if v in stack:
          startIndex = stack.index(v)
          conflictList = stack[startIndex:]
          conflictList.append(v)
          raise ParserException(self, "Cannot construct ordering for computed vector dependencies.\n"
                                      "The vectors causing the conflict are: %s." % ' --> '.join([v.name for v in conflictList]))
        
        # v is not on the stack, so we are safe
        # Put v on the stack
        stack.append(v)
        # Add the dependencies for v at the end of my dependencies
        orderedDependencies.extend(orderedDependenciesForVectors([u for u in v.dependencies if u.isComputed]))
        # Pop v off the stack and put it on our orderedDependencies
        orderedDependencies.append(stack.pop())
      
      return orderedDependencies
    
    computedVectors = [v for v in vectors if v.isComputed]
    return orderedDependenciesForVectors(computedVectors)
  
  def operatorDependenciesForOperatorContainers(self, operatorContainers):
    result = set()
    for operatorContainer in operatorContainers:
      result.update(operatorContainer.operatorDependencies)
    return result
  
  
