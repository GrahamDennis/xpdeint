#!/usr/bin/env python
# encoding: utf-8
"""
_UserLoopCodeBlock.py

Created by Graham Dennis on 2008-09-11.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.ScriptElement import ScriptElement
from xpdeint.ParserException import ParserException

from xpdeint.Function import Function
from xpdeint.Utilities import lazy_property
from xpdeint import CodeLexer
from xpdeint.CallOnceGuards import callOncePerInstanceGuard

from xpdeint.Vectors.ComputedVector import ComputedVector

class _UserLoopCodeBlock(ScriptElement):
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['field', 'space', 'codeString', 'targetVector', 'loopArguments'], KWs)
    
    ScriptElement.__init__(self, **KWs)
    
    self.field = localKWs.get('field')
    self.space = localKWs.get('space')
    if 'codeString' in localKWs: self.codeString = localKWs.get('codeString')
    self.targetVector = localKWs.get('targetVector', None)
    self.loopArguments = localKWs.get('loopArguments', {})
    
    self.bindNamedVectorsCalled = False
    self.preflightCalled = False
  
  @property
  def value(self):
    """
    Defined to make this object look like a ParsedEntity.
    """
    return self.codeString
  
  @lazy_property
  def scriptLineOffset(self):
    """
    Default the script line number offset to be just the line number of the CDATA
    section of our xml element. Though, as with all lazy_property's, this value can
    be overridden.
    """
    return self.xmlElement.lineNumberForCDATASection()
  
  def loop(self, codeWrapperFunction = None, **KWs):
    loopCode = self.codeString
    if codeWrapperFunction: loopCode = codeWrapperFunction(loopCode)
    
    loopKWs = self.loopArguments.copy()
    loopKWs.update(KWs)
    
    result = self.transformVectorsToSpace(self.dependencies, self.space)
    if result: result += '\n'
    loopingVectors = set(self.dependencies)
    if self.targetVector: loopingVectors.add(self.targetVector)
    result += self.loopOverFieldInSpaceWithVectorsAndInnerContent(self.field, self.space, loopingVectors, loopCode, **loopKWs)
    
    return result
  
  @lazy_property
  def codeString(self):
      return self.xmlElement.cdataContents()
  
  @lazy_property
  def specialTargetsVector(self):
    specialTargetsVector = ComputedVector(name = self.parent.id + "_special_targets", field = self.field,
                                          parent = self,
                                          xmlElement = self.xmlElement,
                                          **self.argumentsToTemplateConstructors)
    
    self.field.temporaryVectors.add(specialTargetsVector)
    specialTargetsVector.initialSpace = self.space
    
    # If all dependencies are of type double, then the special targets vector must be double too
    if all([v.type == 'double' for v in self.dependencies]):
      if not self.targetVector or self.targetVector.type == 'double':
        specialTargetsVector.type = 'double'
    
    specialTargetsVector.evaluationSpace = self.space
    specialTargetsVector.integratingComponents = False
    
    evaluationCodeBlock = _TargetConstructorCodeBlock(field = self.field, space = self.space,
                                                      parent = specialTargetsVector,
                                                      **self.argumentsToTemplateConstructors)
    evaluationCodeBlock.targetVector = specialTargetsVector
    specialTargetsVector.codeBlocks['evaluation'] = evaluationCodeBlock
    
    # Call necessary preflight functions on the special targets vector
    if self.bindNamedVectorsCalled: specialTargetsVector.bindNamedVectors()
    if self.preflightCalled:        specialTargetsVector.preflight()
    
    self._children.append(specialTargetsVector)
    
    return specialTargetsVector
  
  def addCodeStringToSpecialTargetsVector(self, codeString, containingCodeSlice):
    specialTargetsVector = self.specialTargetsVector
    specialTargetCodeBlock = specialTargetsVector.codeBlocks['evaluation']
    
    targetCodeBlocks = specialTargetCodeBlock.targetCodeBlocks
    codeBlocksWithSameTarget = [codeBlock for codeBlock in targetCodeBlocks if codeBlock.codeString == codeString]
    if codeBlocksWithSameTarget:
      evaluationCodeBlock = codeBlocksWithSameTarget[0]
      targetVariableName = 'target%i' % targetCodeBlocks.index(evaluationCodeBlock)
    else:
      evaluationCodeBlock = _UserLoopCodeBlock(field = self.field, space = self.space,
                                               parent = specialTargetCodeBlock,
                                               xmlElement = self.xmlElement,
                                               **self.argumentsToTemplateConstructors)
      evaluationCodeBlock.codeString = codeString
      # This code block could depend on anything we do
      evaluationCodeBlock.dependencies.update(self.dependencies)
      evaluationCodeBlock.scriptLineOffset = self.scriptLineOffset + self.codeString.count('\n', 0, containingCodeSlice.start)
      targetCodeBlocks.append(evaluationCodeBlock)
      targetVariableName = 'target%i' % targetCodeBlocks.index(evaluationCodeBlock)
      specialTargetsVector.components.append(targetVariableName)
      
      # Call necessary preflight functions on the code block
      if self.bindNamedVectorsCalled: evaluationCodeBlock.bindNamedVectors()
      if self.preflightCalled:        evaluationCodeBlock.preflight()
    
    return targetVariableName
  
  def fixupComponentsWithIntegerValuedDimensions(self):
    """
    In user code, the user may refer to parts of a vector nonlocally in integer-valued dimensions.
    This code translates variables accessed with the ``phi[j-3, k+5, l/2][p*p, q, r]`` notation to a form
    that can be used in the C++ source file. The form currently used is ``_phi(j-3, k+5, l/2, p*p, q, r)``
    and this is defined as a macro by the appropriate `ScriptElement` looping function.
    
    This function makes an optimisation where if all integer-valued dimensions are accessed locally,
    the ``phi[j, k, l][p, q, r]`` notation is replaced with the string ``phi`` which is a faster
    way of accessing the local value than through using the ``_phi(...)`` macro.
    """
    vectorsToFix = self.dependencies.copy()
    if self.targetVector: vectorsToFix.add(self.targetVector)
    
    if self.getVar('geometry').integerValuedDimensions and vectorsToFix:
      simulationDriver = self.getVar('features')['Driver']
      for componentName, field, integerDimDict, codeSlice in reversed(CodeLexer.integerValuedDimensionsForVectors(vectorsToFix, self)):
        # We know that integerDimDict is non-empty
        
        integerValuedDimensions = field.integerValuedDimensions
        
        integerValuedDimensionNames = []
        for dimList in integerValuedDimensions:
          integerValuedDimensionNames.extend([dim.name for dim in dimList])
        
        # We can do an optimisation here, components accessed with the 'normal' pattern
        # can be stripped of the integer-valued dimension specifiers. i.e.
        # phi[j, k] can become just 'phi' if the first integer-valued dimension is 'j' and
        # the second is 'k'.
        
        canOptimiseIntegerValuedDimensions = all([integerDimDict[dimName][0] == dimName for dimName in integerValuedDimensionNames])
        
        if canOptimiseIntegerValuedDimensions:
          replacementString = componentName
        else:
          # It would be illegal to try and access any distributed dimensions nonlocally, so we need to check for this.
          for dim in field.dimensions:
            if dim.name in simulationDriver.distributedDimensionNames and dim.name in integerValuedDimensionNames:
              if not integerDimDict[dim.name][0] == dim.name:
                dimName = dim.name
                raise ParserException(self.xmlElement, "It is illegal to access the dimension '%(dimName)s' nonlocally because it is being distributed with MPI.\n"
                                                       "Try not using MPI or changing the order of your dimensions." % locals())
          
          argumentsString = ', '.join([integerDimDict[dimName][0] for dimName in integerValuedDimensionNames])
          
          replacementString = '_%(componentName)s(%(argumentsString)s)' % locals()
        
        # Replace the phi[j] string with the appropriate string
        self.codeString = self.codeString[:codeSlice.start] + replacementString + self.codeString[codeSlice.stop:]
    
  
  def transformCodeString(self):
    """Modify the user code as necessary."""
    self.fixupComponentsWithIntegerValuedDimensions()
    
    if self.codeString.count('\n'):
      # Deindent code and add '#line' compiler directives
      self.codeString = self.insertUserCodeFromEntity(self)
    
  @callOncePerInstanceGuard
  def bindNamedVectors(self):
    # This function would be called twice otherwise because it gets called specially
    # by the _ScriptElement implementation of bindNamedVectors
    super(_UserLoopCodeBlock, self).bindNamedVectors()
    self.bindNamedVectorsCalled = True
  
  @callOncePerInstanceGuard
  def preflight(self):
    super(_UserLoopCodeBlock, self).preflight()
    
    self.transformCodeString()
    
    self.preflightCalled = True
  

class _TargetConstructorCodeBlock(_UserLoopCodeBlock):
  def __init__(self, **KWs):
    _UserLoopCodeBlock.__init__(self, **KWs)
    
    self.targetCodeBlocks = []
  
  scriptLineOffset = 0
  
  @property
  def children(self):
    children = super(_TargetConstructorCodeBlock, self).children
    children.extend(self.targetCodeBlocks)
    return children
  
  @property
  def dependencies(self):
    dependencies = set()
    # Add all the dependencies of all target code blocks together
    for targetCodeBlock in self.targetCodeBlocks:
      dependencies.update(targetCodeBlock.dependencies)
    return frozenset(dependencies)
  
  @property
  def codeString(self):
    return ''.join(['target%i = %s;\n' % (targetNum, targetCodeBlock.codeString) for targetNum, targetCodeBlock in enumerate(self.targetCodeBlocks)])
  
  def transformCodeString(self):
    # This will be done as needed for all child code blocks
    pass
  
  
  