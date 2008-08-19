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
from xpdeint.ParserException import ParserException

import re
from xpdeint import RegularExpressionStrings

class _ScriptElement (Template):
  class LoopingOrder(object):
    MemoryOrder = 1
    StrictlyAscendingOrder = 2
    StrictlyDescendingOrder = 3
  
  argumentsToTemplateConstructors = {}
  # Initialise the callOnceGuards to be empty
  _callOnceGuards = set()
  _callOncePerInstanceGuards = dict()
  
  @classmethod
  def resetGuards(cls):
    """
    Reset the flags used by the `CallOnceGuards` function decorators to ensure that
    various functions are only called once.
    
    Calling these functions causes all of these flags to be reset to `False` causing
    the functions protected by the `CallOnceGuards` function decorators to be able
    to be called again.
    """
    _ScriptElement._callOnceGuards.clear()
    for instanceGuardSet in _ScriptElement._callOncePerInstanceGuards.itervalues():
      instanceGuardSet.clear()
  
  __driver = None
  
  @property
  def _driver(self):
    """
    Return the simulation driver, but cache the result in a variable shared between
    all `_ScriptElement` instances.
    """
    if not _ScriptElement.__driver:
      _ScriptElement.__driver = self.getVar('features')['Driver']
    return _ScriptElement.__driver
  
  
  _ScriptElement_haveCalledInit = False
  
  def __init__(self, *args, **KWs):
    # If we have a diamond-inheritence, this function could be called more than once
    # And that would be bad. Let's check for that case, and return if it is the case.
    # Template can deal with being called more than once, but some of the code below
    # wouldn't be safe called more than once
    if self._ScriptElement_haveCalledInit:
      return
    
    self._ScriptElement_haveCalledInit = True
    
    localKWs = self.extractLocalKWs(['xmlElement', 'parent'], KWs)
    
    Template.__init__(self, *args, **KWs)
    
    self.getVar('templates').add(self)
    
    # Only set the dependencies attribute if it isn't taken
    # care of elsewhere
    if not hasattr(type(self), 'dependencies'):
      self.dependencies = set()
    
    self._parent = localKWs.get('parent', None)
    self._propagationDimension = None
    self._propagationDirection = None
    self.xmlElement = localKWs.get('xmlElement', None)
    self.dependenciesEntity = None
    self.functions = {}
    self._id = None
    self._haveBeenRemoved = False
    
    if self.hasattr('globalNameSpaceName'):
      globalNameSpace = KWs['searchList'][0]
      globalNameSpace[self.globalNameSpaceName] = self
      if not self in globalNameSpace['scriptElements']:
        globalNameSpace['scriptElements'].append(self)
    
    # Create the entry in the callOnceGuards
    _ScriptElement._callOncePerInstanceGuards[self] = set()
  
  @property
  def parent(self):
    """
    Return the parent template of this template. Note that the return value may be `None`.
    
    The parent of the template is defined as the template that has this template as a member
    of the `children` attribute of that instance. Should multiple templates meet this requirement
    an exception will be raised.
    """
    if self._parent:
      return self._parent
    
    potentialParents = filter(lambda x: x.hasattr('children') and id(self) in map(id, x.children), self.getVar('templates'))
    
    if not potentialParents:
      return None
    
    if len(potentialParents) > 1:
      raise AssertionError("We seem to have more than one parent: " + ', '.join([repr((potentialParent, potentialParent.id)) for potentialParent in potentialParents]))
    
    self._parent = potentialParents[0]
    return self._parent
  
  @property
  def id(self):
    """
    Return a string that should uniquely identify this object.
    
    The string returned will be appropriate for use as a `C` variable name and
    will begin with and underscore.
    """
    if not self._id:
      if not self.parent or not self.parent.id:
        self._id = self.name
      else:
        self._id = '_'.join([self.parent.id, self.name])
    return self._id
  
  @property
  def noiseField(self):
    """
    The field that noises should be evaluated in for this object.
    This defaults to `field`, but can be overridden by subclasses.
    """
    return self.field
  
  def _getPropagationDimension(self):
    """
    Return the name of the current propagation dimension for this template. Note that this
    does not need to be the same as the propagation dimension for the entire simulation because
    cross-propagation works by using a standard integrator, but by setting a different propagation
    dimension.
    
    This function is used in the creation of the `propagationDimension` property.
    """
    
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
    """
    Return a string representing the sign of the direction of propagation. This string will
    either be '+' or '-'. Note that usually this will be '+', however it will be '-' for
    cross-propagators that have a 'right' boundary condition.
    
    This method is used in the creation of the `propagationDirection` property.
    """
    if self._propagationDirection:
      return self._propagationDirection
    
    if self.parent:
      self._propagationDirection = self.parent.propagationDirection
    else:
      self._propagationDirection = '+'
    
    return self._propagationDirection
  
  def _setPropagationDirection(self, value):
    self._propagationDirection = value
  
  propagationDirection = property(_getPropagationDirection, _setPropagationDirection)
  del _getPropagationDirection, _setPropagationDirection
  
  def hasattr(self, attrName):
    """
    Helper method to return whether or not the instance has the attribute `attrName`.
    The difference between this method and the Python `hasattr` function is that this one
    will raise an exception if the attribute `attrName` does exist but accessing it would
    cause an exception to be raised.
    """
    try:
      getattr(self, attrName)
    except AttributeError, err:
      if hasattr(type(self), attrName):
        raise
      return False
    else:
      return True
  
  def valueForKeyPath(self, keyPath):
    """
    Return the value for a dotted-name lookup of `keyPath` antichored at `self`.
    
    This is similar to the KVC methods in Objective-C, however its use is appropriate in Python.
    Evaluating the `keyPath` 'foo.bar.baz' returns the object that would be returned by evaluating
    the string (in Python) self.foo.bar.baz
    """
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
    if not self.functions:
      return
    return ''.join([f.prototype() for f in self.functions.itervalues() if f.predicate()])
  
  # Function implemenations
  def functionImplementations(self):
    if not self.functions:
      return
    return '\n\n'.join([f.implementation() for f in self.functions.itervalues() if f.predicate()])
  
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
    """
    This function is at the core of the 'Feature' system used by xpdeint. Its design is kinda
    like aspect-oriented programming in that the idea is to separate code that is logically separate
    but required in a large number of places. The idea behind this system is the creation of a 
    number of named 'insertion points' in the generated C++ code where features can insert code
    if they need to. Usually these insertion points come in pairs called 'someFunctionNameBegin'
    and 'someFunctionNameEnd' that are at balanced points in the code.
    
    The 'Feature' system diverges from the usual Aspect-Oriented programming approach in that when
    you specify the insertion point, you also specify the features that you want to be able to insert
    code at that point and the order in which they should be able to insert code. This allows for a
    sensible balancing of the inserted code such that when code from multiple features is inserted
    at a 'someFunctionBegin' insertion point, by calling the `insertCodeForFeaturesInReverseOrder`
    method at the 'someFunctionEnd' insertion point, the code necessary for these features at this
    insertion point is inserted in the opposite order than for 'someFunctionBegin'.
    
    The optional `dict` argument can be used to pass additional variables to the features. The 
    `reverse` argument should not be used, it is used internally by `insertCodeForFeaturesInReverseOrder`.
    """
    featureDictionary = self.getVar('features')
    
    if not dict:
        dict = {}
    
    if self.hasattr('bannedFeatures') and self.bannedFeatures:
      # Check if any of the features in the featureList are in the bannedFeatures
      bannedFeatures = self.bannedFeatures
      featureList = filter(lambda x: x not in bannedFeatures, featureList)
    
    result = []
    filt = self._CHEETAH__currentFilter
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
        result.append(filt(featureResult, extraIndent=extraIndent))
      else:
        # If we're doing this in reverse order, then we use the final indent as the indent for the result
        result.append(filt(featureResult, extraIndent=dict.get('extraIndent', 0)))
    
    return ''.join(result)
  
  # Insert code for a list of features (in reverse order) by calling a named function
  def insertCodeForFeaturesInReverseOrder(self, functionName, featureList, dict = None):
    # Create a reversed feature list
    reversedFeatureList = featureList[:]
    reversedFeatureList.reverse()
    
    return self.insertCodeForFeatures(functionName, reversedFeatureList, dict, reverse=True)
  
  def dimensionIsInFourierSpace(self, dimension, space):
    """Return `True` if `dimension` is in fourier space in `space`."""
    geometryDimensionNumber = self.getVar('geometry').indexOfDimension(dimension)
    if space & (1 << geometryDimensionNumber):
      # This dimension is in fourier space
      return True
    else:
      # This dimension isn't in fourier space
      return False
  
  # Return the name of the dimension considering the current space
  def dimensionNameForSpace(self, dimension, space):
    """
    Return the name for `dimension` in `space`. If the dimension is in fourier
    space, then the dimension name is kDimensionName if the dimension's normal name
    is 'DimensionName'.
    """
    if self.dimensionIsInFourierSpace(dimension, space):
      return 'k' + dimension.name
    else:
      return dimension.name
  
  # Insert contents of function for self, classes and children
  def implementationsForFunctionName(self, functionName, *args, **KWs):
    """
    Helper function to call the function `functionName` for this instance, its
    class and its children and return the combined result as a string.
    """
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
        childFunctionOutput = child.implementationsForFunctionName(functionName, *args, **KWs)
        if childFunctionOutput and not childFunctionOutput.isspace():
          result.append(blankLineSeparator)
          blankLineSeparator = '\n'
          result.append(childFunctionOutput)
    
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
    """
    Part of the 'preflight' system. Once templates have been parsed, a template should
    implement this method if it needs to bind the name of a vector to the actual vector
    object itself and check if it even exists.
    """
    if self.dependenciesEntity:
      self.dependencies.update(self.vectorsFromEntity(self.dependenciesEntity))
    
  
  def preflight(self):
    """
    Part of the 'preflight' system. This function is guaranteed to be called after `bindNamedVectors`
    has been called on all templates. This is where other post-parsing code goes before the simulation
    is converted to a C++ source file.
    """
    pass
  
  def vectorsFromEntity(self, entity):
    """
    Given the `ParsedEntity` `entity`, return the set of vectors corresponding to the list of names
    in the value of the XML element contained by the entity.
    """
    vectors = set()
    vectorDictionary = dict([(vector.name, vector) for vector in self.getVar('vectors')])
    
    ancestors = []
    currObject = self
    while currObject:
      ancestors.append(currObject)
      currObject = currObject.parent
    
    for vectorName in entity.value:
      vector = None
      replacementVector = None
      if self.parent:
        replacementVector = self.parent.vectorForVectorName(vectorName, vectorDictionary)
      
      if not vectorName in vectorDictionary:
        raise ParserException(entity.xmlElement, "Unknown vector '%(vectorName)s'." % locals())
      else:
        vector = vectorDictionary[vectorName]
      
      if not (vector.parent == vector.field or vector.parent in ancestors):
        raise ParserException(entity.xmlElement, "Cannot access vector '%(vectorName)s' here. It is not available in this scope." % locals())
      
      if replacementVector:
        vectors.add(replacementVector)
      else:
        vectors.add(vector)
    return vectors
  
  def vectorForVectorName(self, vectorName, vectorDictionary):
    """
    Function that can be used by a template to override the mapping of vector names to vectors for children
    """
    if self.parent:
      return self.parent.vectorForVectorName(vectorName, vectorDictionary)
  
  
  def transformVectorsToSpace(self, vectors, space):
    """Transform vectors `vectors` to space `space`."""
    result = []
    for vector in vectors:
      if not (vector.initialSpace) == (space & vector.field.spaceMask):
        if not vector.isTransformableTo(space):
          raise ParserException(self.xmlElement,
                  "Cannot satisfy dependence on vector '%s' because it cannot "
                  "be transformed to the appropriate space." % vector.name)
      if vector.needsTransforms:
        result.extend([vector.functions['goSpace'].call(_newSpace=space), '\n'])
      # Add space $space to the set of spaces in which this vector is needed
      vector.spacesNeeded.add(space & vector.field.spaceMask)
    return ''.join(result)
  
  
  def remove(self):
    """
    Remove the template from various global lists that it may have got itself into. This method
    should be called if a template is no longer needed and should be deleted.
    """
    self.getVar('templates').discard(self)
    scriptElements = self.getVar('scriptElements')
    
    for someIterable in (self.getVar('scriptElements'), self.getVar('fields'),
                         self.getVar('vectors'), self.getVar('momentGroups')):
      while self in someIterable:
        someIterable.remove(self)
    
    if self.hasattr('children'):
      for child in self.children:
        child.remove()
    
    self._haveBeenRemoved = True
  
  def fixupComponentsWithIntegerValuedDimensions(self, vectors, code):
    """
    In user code, the user may refer to parts of a vector nonlocally in integer-valued dimensions.
    This code translates variables accessed with the ``phi[j-3, k+5, l/2][p*p, q, r]`` notation to a form
    that can be used in the C++ source file. The form currently used is ``_phi(j-3, k+5, l/2, p*p, q, r)``
    and this is defined as a macro by the appropriate `ScriptElement` looping function.
    
    This function makes an optimisation where if all integer-valued dimensions are accessed locally,
    the ``phi[j, k, l][p, q, r]`` notation is replaced with the string ``phi`` which is a faster
    way of accessing the local value than through using the ``_phi(...)`` macro.
    """
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
        regex = re.compile(RegularExpressionStrings.integerValuedDimensionsForComponentInField(componentName, vector.field),
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
          # It would be illegal to try and access any distributed dimensions nonlocally, so we need to check for this.
          for dim in vector.field.dimensions:
            simulationDriver = self.getVar('features')['Driver']
            if dim.name in simulationDriver.distributedDimensionNames and dim.name in integerValuedDimensionNames:
              if not integerValuedDimensionsMatch.group(dim.name).strip() == dim.name:
                dimName = dim.name
                raise ParserException(self.xmlElement, "It is illegal to access the dimension '%(dimName)s' nonlocally because it is being distributed with MPI.\n"
                                                       "Try not using MPI or changing the order of your dimensions." % locals())
          
          argumentsString = ', '.join([integerValuedDimensionsMatch.group(dimName).strip() for dimName in integerValuedDimensionNames])
          
          replacementString = '_%(componentName)s(%(argumentsString)s)' % locals()
        
        # Create a regular expression to replace the phi[j] string with the appropriate string
        operatorCodeReplacementRegex = re.compile(r'\b' + re.escape(componentName) + re.escape(match.group('integerValuedDimensions')))
        
        code = operatorCodeReplacementRegex.sub(replacementString, code, count = 1)
    
    return code
  
  def templateObjectFromStringWithTemplateVariables(self, templateString, templateVars):
    """
    Return a Cheetah template object (using the appropriate settings) for `templateString`
    with the dictionary `templateVars` as variables available in the template.
    """
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
  
  def computedVectorsNeedingPrecalculationForOperatorContainers(self, operatorContainers):
    """
    Return a set of computed vectors that `operatorContainers` need to be precomputed
    before executing the operator containers.
    """
    result = set()
    for operatorContainer in operatorContainers:
      result.update(operatorContainer.computedVectorsNeedingPrecalculation)
    return result
  
  def mayHaveLocalOffsetForDimensionInFieldInSpace(self, dimension, field, space):
    """
    Return `True` if this dimension may have a local offset. This should only be true
    when `dimension` is being distributed with MPI.
    """
    return self._driver.mayHaveLocalOffsetForDimensionInFieldInSpace(dimension, field, space)
  
  def localOffsetForDimensionInFieldInSpace(self, dimension, field, space):
    return self._driver.localOffsetForDimensionInFieldInSpace(dimension, field, space)
  
  def localLatticeForDimensionInFieldInSpace(self, dimension, field, space):
    return self._driver.localLatticeForDimensionInFieldInSpace(dimension, field, space)
  
  def sizeOfVectorInSpace(self, vector, space):
    return ''.join([self.sizeOfFieldInSpace(vector.field, space), ' * _', vector.id, '_ncomponents'])
  
  def sizeOfVectorInSpaceInReals(self, vector, space):
    if vector.type == 'double':
      return self.sizeOfVectorInSpace(vector, space)
    else:
      return '2 * ' + self.sizeOfVectorInSpace(vector, space)
  
  def allocSizeOfVector(self, vector):
    return ''.join([self.allocSizeOfField(vector.field), ' * _', vector.id, '_ncomponents'])
  
  def allocSizeOfField(self, field):
    return self._driver.allocSizeOfField(field)
  
  def sizeOfVector(self, vector):
    return self._driver.sizeOfVector(vector)
  
  def sizeOfFieldInSpace(self, field, space):
    """Return a name of a variable the value of which is the size of `field` in `space`."""
    return self._driver.sizeOfFieldInSpace(field, space)
  
  def orderedDimensionsForFieldInSpace(self, field, space):
    """Return a list of the dimensions for field in the order in which they should be looped over"""
    return self._driver.orderedDimensionsForFieldInSpace(field, space)
  
  @staticmethod
  def extractLocalKWs(legalKWs, KWs):
    result = {}
    for key in KWs.copy():
      if key in legalKWs:
        result[key] = KWs[key]
        del KWs[key]
    return result
    
  
