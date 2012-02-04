#!/usr/bin/env python
# encoding: utf-8
"""
_ScriptElement.py

This contains all the pure-python code for ScriptElement.tmpl

Created by Graham Dennis on 2007-10-17.
Copyright (c) 2007-2012 Graham Dennis.

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

import textwrap

from Cheetah.Template import Template
from xpdeint.ParserException import ParserException

from xpdeint.Utilities import lazy_property

class _ScriptElement (Template):
  class LoopingOrder(object):
    MemoryOrder = 1
    StrictlyAscendingOrder = 2
    StrictlyDescendingOrder = 3
  
  argumentsToTemplateConstructors = {}
  # Initialise the callOnceGuards to be empty
  _callOnceGuards = set()
  _callOncePerInstanceGuards = dict()
  
  simulation = None
  
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
  
  @property
  def _driver(self):
    """
    Return the simulation driver, but cache the result in a variable shared between
    all `_ScriptElement` instances.
    """
    _ScriptElement._driver = self.getVar('features')['Driver']
    return _ScriptElement._driver
  
  
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
    
    assert 'parent' in localKWs
    self.parent = localKWs['parent']
    
    if self.parent and self.parent == self.simulation:
      self.simulation._children.append(self)
    self.xmlElement = localKWs.get('xmlElement', None)
    self.dependenciesEntity = None
    self.functions = {}
    self.codeBlocks = {}
    self._haveBeenRemoved = False
    
    self._children = []
    
    if hasattr(type(self), 'globalNameSpaceName'):
      globalNameSpace = KWs['searchList'][0]
      globalNameSpace[self.globalNameSpaceName] = self
    
    # Create the entry in the callOnceGuards
    _ScriptElement._callOncePerInstanceGuards[self] = set()
  
  @lazy_property
  def id(self):
    """
    Return a string that should uniquely identify this object.
    
    The string returned will be appropriate for use as a ``C`` variable name and
    will begin with and underscore.
    """
    if not self.parent or not self.parent.id:
      return self.name
    else:
      return '_'.join([self.parent.id, self.name])
  
  @property
  def children(self):
    result = self._children[:]
    result.extend(self.codeBlocks.values())
    return result
  
  @lazy_property
  def propagationDimension(self):
    """
    Return the name of the current propagation dimension for this template. Note that this
    does not need to be the same as the propagation dimension for the entire simulation because
    cross-propagation works by using a standard integrator, but by setting a different propagation
    dimension.
    """
    
    if self.parent:
      return self.parent.propagationDimension
    
    return self.getVar("globalPropagationDimension")
  
  @lazy_property
  def propagationDirection(self):
    """
    Return a string representing the sign of the direction of propagation. This string will
    either be '+' or '-'. Note that usually this will be '+', however it will be '-' for
    cross-propagators that have a 'right' boundary condition.
    
    This method is used in the creation of the `propagationDirection` property.
    """
    if self.parent:
      return self.parent.propagationDirection
    else:
      return '+'
  
  @lazy_property
  def scriptLineNumber(self):
    return self.xmlElement.lineNumberForCDATASection()
  
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
  
  def allocate(self):   return self.implementationsForChildren('allocate')
  def free(self):       return self.implementationsForChildren('free')
  
  def initialise(self): return self.implementationsForChildren('initialise')
  def finalise(self):   return self.implementationsForChildren('finalise')
  
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
    
    for codeBlock in self.codeBlocks.itervalues():
      # Warning: This means that codeBlocks will have bindNamedVectors() called twice.
      codeBlock.bindNamedVectors()
    
  
  def preflight(self):
    """
    Part of the 'preflight' system. This function is guaranteed to be called after `bindNamedVectors`
    has been called on all templates. This is where other post-parsing code goes before the simulation
    is converted to a C++ source file.
    """
    if hasattr(self, 'uselib'):
      self.getVar('simulationUselib').update(self.uselib)
    if hasattr(self, 'buildVariant'):
      buildVariant = self.getVar('simulationBuildVariant')
      if buildVariant and not self.buildVariant in buildVariant:
        raise ParserException(self, "Internal Error. More than one build variant is trying to be used.\n"
                                    "Please report this error to %s\n" % self.getVar('bugReportAddress'))
      buildVariant.add(self.buildVariant)
    
  
  def vectorsFromEntity(self, entity):
    """
    Given the `ParsedEntity` `entity`, return the set of vectors corresponding to the list of names
    in the value of the XML element contained by the entity.
    """
    vectors = set()
    vectorDictionary = dict([(vector.name, vector) for vector in self.getVar('simulationVectors')])
    
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
  
  def basisIndexForBasis(self, basis):
    transformMultiplier = self.getVar('features')['TransformMultiplexer']
    return transformMultiplier.basesNeeded.index(basis)
  
  def transformVectorsToBasis(self, vectors, basis):
    result = []
    for vector in vectors:
      if not vector.needsTransforms:
        continue
      vectorBasis = vector.field.basisForBasis(basis)
      if not vector.isTransformableTo(vectorBasis):
        raise ParserException(
          self.xmlElement,
          "Cannot satisfy dependence on vector '%s' because it cannot be transformed to the required basis (%s). "
          "The vector's initial basis is (%s)." % (vector.name, ', '.join(vectorBasis), ', '.join(vector.initialBasis))
        )
      basisString = ', '.join(vectorBasis)
      basisIndex = self.basisIndexForBasis(vectorBasis)
      result.extend([vector.functions['basisTransform'].call(new_basis=basisIndex), ' // (', basisString, ')\n'])
    return ''.join(result)
  
  def registerVectorsRequiredInBasis(self, vectors, basis):
    for vector in vectors:
      vector.basesNeeded.add(vector.field.basisForBasis(basis))
  
  def remove(self):
    """
    Remove the template from various global lists that it may have got itself into. This method
    should be called if a template is no longer needed and should be deleted.
    """
    self.getVar('templates').discard(self)
    
    for someIterable in (self.parent.children, self.getVar('fields'),
                         self.getVar('simulationVectors'), self.getVar('momentGroups')):
      while self in someIterable:
        someIterable.remove(self)
    
    if self.hasattr('children'):
      for child in self.children:
        child.remove()
    
    self._haveBeenRemoved = True
  
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
  
  
  def evaluationOrderForVectors(self, vectors, static, predicate = lambda x: True):
    """
    Return the ordering for the noise vectors and computed vectors in `vectors` taking into account
    any dependencies between the computed vectors.
    """
    
    def checkSelfConsistentVectors(vectors, static):
      #We check that all noise vectors are static or dynamic, as requested.
      for nv in [nv for nv in vectors if nv.isNoise and nv.static != static]:
        if static:
            raise ParserException(self.xmlElement, "Dynamic noises (Wiener and Jump processes) cannot be used outside of integration elements.\n"
                                                   "Perhaps %s should be a static noise (like 'Gaussian' or 'Poissonian')?" % nv.name)
        if not static:
            raise ParserException(self.xmlElement, "Static noises cannot be used inside integration elements.\n"
                                                   "Perhaps %s should be a dynamic noise (like 'Wiener' or 'Jump')?" % nv.name)
          
    stack = []
    
    checkSelfConsistentVectors(vectors, static)
    
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
      checkSelfConsistentVectors(vectors, static)
      
      for v in vectors:
        # If v is in the ordering, then it has already been taken care of
        if v in orderedDependencies:
          continue
        
        # If v is on the stack, then we have a circular dependency
        if v in stack:
          startIndex = stack.index(v)
          conflictList = stack[startIndex:]
          conflictList.append(v)
          raise ParserException(self.xmlElement, "Cannot construct ordering for computed vector dependencies.\n"
                                                 "The vectors causing the conflict are: %s." % ' --> '.join([v.name for v in conflictList]))
        
        # v is not on the stack, so we are safe
        # Put v on the stack
        stack.append(v)
        # Add the dependencies for v at the end of my dependencies if they aren't there already
        newDependencies = orderedDependenciesForVectors([u for u in v.dependencies if predicate(u)])
        orderedDependencies.extend([v for v in newDependencies if not v in orderedDependencies])
        # Pop v off the stack and put it on our orderedDependencies
        orderedDependencies.append(stack.pop())
      
      return orderedDependencies
    
    return orderedDependenciesForVectors([v for v in vectors if predicate(v)])
  
  def dynamicVectorsNeedingPrecalculationForOperatorContainers(self, operatorContainers):
    """
    Return a set of computed vectors that `operatorContainers` need to be precomputed
    before executing the operator containers.
    """
    result = set()
    for operatorContainer in operatorContainers:
      result.update(operatorContainer.dynamicVectorsNeedingPrecalculation)
    return result
  
  @staticmethod
  def extractLocalKWs(legalKWs, KWs):
    result = {}
    for key in KWs.copy():
      if key in legalKWs:
        result[key] = KWs[key]
        del KWs[key]
    return result
    
  
  def wrapArray(self, array):
    return '\n  ' + textwrap.fill(', '.join([repr(float(e)) for e in array]), subsequent_indent='  ') + '\n  '
  
