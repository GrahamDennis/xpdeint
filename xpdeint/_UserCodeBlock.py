#!/usr/bin/env python
# encoding: utf-8
"""
_UserCodeBlock.py

Created by Graham Dennis on 2008-09-11.

Copyright (c) 2008-2012, Graham Dennis

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

from xpdeint.Utilities import lazy_property
from xpdeint import CodeParser
from xpdeint.CodeParser import CodeParserException
from xpdeint.CallOnceGuards import callOncePerInstanceGuard

from xpdeint.Vectors.ComputedVector import ComputedVector

import textwrap

class _UserCodeBlock(ScriptElement):
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['codeString'], KWs)
    
    ScriptElement.__init__(self, **KWs)
    
    if 'codeString' in localKWs: self.codeString = localKWs.get('codeString')
  
  @lazy_property
  def codeString(self):
    return self.xmlElement.cdataContents()
  
  def transformCodeString(self):
    CodeParser.checkForIntegerDivision(self)
    
    if self.codeString.count('\n'):
      # Deindent code and add '#line' compiler directives
      self.addCompilerLineDirectives()
    
  
  def addCompilerLineDirectives(self):
    """
    Add the #line compiler directives at the start and end so that
    any compiler errors are reported in terms of lines in the actual xmds
    script itself.
    """
    result = [textwrap.dedent(self.codeString)]
    
    writeLineDirectives = not self.getVar('debug') and self.xmlElement
    if writeLineDirectives:
      result.insert(
        0,
        '#line %i "%s"\n' % (self.scriptLineNumber, self.getVar('scriptName'))
      )
      result.append('\n#line _XPDEINT_CORRECT_MISSING_LINE_NUMBER_\n')
    self.codeString = ''.join(result)
  
  def preflight(self):
    super(_UserCodeBlock, self).preflight()
    self.transformCodeString()
  

class _UserLoopCodeBlock(_UserCodeBlock):
  def __init__(self, **KWs):
    localKWs = self.extractLocalKWs(['field', 'basis', 'targetVector', 'loopArguments'], KWs)
    
    _UserCodeBlock.__init__(self, **KWs)
    
    self.field = localKWs.get('field')
    self.basis = localKWs.get('basis')
    
    self.targetVector = localKWs.get('targetVector', None)
    self.loopArguments = localKWs.get('loopArguments', {})
    
    self.bindNamedVectorsCalled = False
    self.preflightCalled = False
    
    self.prefixCodeString = ''
    self.postfixCodeString = ''
  
  @property
  def loopCodeString(self):
    return self.prefixCodeString + self.codeString + self.postfixCodeString
  
  def loop(self, codeWrapperFunction = None, **KWs):
    loopCode = self.loopCodeString
    if codeWrapperFunction: loopCode = codeWrapperFunction(loopCode)
    
    loopKWs = self.loopArguments.copy()
    loopKWs.update(KWs)
    
    result = self.transformVectorsToBasis(self.dependencies, self.basis)
    if result: result = "// Transforming vectors to basis (%s)\n%s\n" % (', '.join(self.basis), result)
    loopingVectors = set(self.dependencies)
    if self.targetVector: loopingVectors.add(self.targetVector)
    result += self.loopOverFieldInBasisWithVectorsAndInnerContent(self.field, self.basis, loopingVectors, loopCode, **loopKWs)
    
    return result
  
  @lazy_property
  def specialTargetsVector(self):
    # If all dependencies are of type real, then the special targets vector must be real too
    specialTargetsVectorType = 'complex'
    if all([v.type == 'real' for v in self.dependencies]):
      if not self.targetVector or self.targetVector.type == 'real':
        specialTargetsVectorType = 'real'
    
    specialTargetsVector = ComputedVector(name = self.parent.id + "_special_targets", field = self.field,
                                          parent = self, initialBasis = self.basis,
                                          type = specialTargetsVectorType, xmlElement = self.xmlElement,
                                          **self.argumentsToTemplateConstructors)
    
    self.field.temporaryVectors.add(specialTargetsVector)
    
    specialTargetsVector.integratingComponents = False
    
    evaluationCodeBlock = _TargetConstructorCodeBlock(
      field = self.field, basis = self.basis,
      parent = specialTargetsVector,
      **self.argumentsToTemplateConstructors
    )
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
      evaluationCodeBlock = _UserLoopCodeBlock(
        field = self.field, basis = self.basis,
        parent = specialTargetCodeBlock, xmlElement = self.xmlElement,
        **self.argumentsToTemplateConstructors
      )
      evaluationCodeBlock.codeString = codeString
      # This code block could depend on anything we do
      evaluationCodeBlock.dependencies.update(self.dependencies)
      evaluationCodeBlock.scriptLineNumber = self.scriptLineNumber + self.codeString.count('\n', 0, containingCodeSlice.start)
      targetCodeBlocks.append(evaluationCodeBlock)
      targetVariableName = 'target%i' % targetCodeBlocks.index(evaluationCodeBlock)
      specialTargetsVector.components.append(targetVariableName)
      
      # Call necessary preflight functions on the code block
      if self.bindNamedVectorsCalled: evaluationCodeBlock.bindNamedVectors()
      if self.preflightCalled:        evaluationCodeBlock.preflight()
    
    return targetVariableName
  
  def fixupNonlocallyAccessedComponents(self):
    """
    In user code, the user may refer to parts of a vector nonlocally in integer-valued dimensions.
    This code translates variables accessed with the ``phi(j: j-3, k:k+5, l:l/2, p:p*p, q:q, r:r)`` notation to a form
    that can be used in the C++ source file. The form currently used is ``_phi_jklpqr(j-3, k+5, l/2, p*p, q, r)``.
    
    This function makes an optimisation where if all dimensions are accessed locally,
    the ``phi(j: j, k:k, l:l, p:p, q: q, r: r)`` notation is replaced with the string ``phi`` which is a faster
    way of accessing the local value than through using the ``_phi_jklpqr(...)`` macro.
    """
    vectorsToFix = self.dependencies.copy()
    if self.targetVector: vectorsToFix.add(self.targetVector)
    
    nonlocalVariablesCreated = set()
    
    vectorOverrides = self.loopArguments.get('vectorOverrides', [])
    
    simulationDriver = self.getVar('features')['Driver']
    for componentName, vector, nonlocalAccessDict, codeSlice in reversed(CodeParser.nonlocalDimensionAccessForVectors(vectorsToFix, self)):
      availableDimReps = vector.field.inBasis(self.basis)
      validDimensionNames = [dimRep.name for dimRep in availableDimReps]
      validDimensionNames.extend([dimRep.name + "_index" for dimRep in availableDimReps])
      
      # If the dict is empty, then it probably means something else
      if not nonlocalAccessDict:
        continue
      
      if vector in vectorOverrides:
        vectorID = vector.id
        raise CodeParserException(self, codeSlice.start, "Cannot access vector '%(vectorID)s' non-locally." % locals())
      
      # Check that there are no dimensions listed in the nonlocalAccessDict that don't refer to valid
      # dimensions for this vector
      
      for dimName in nonlocalAccessDict.iterkeys():
        if not dimName in validDimensionNames:
          raise CodeParserException(self, nonlocalAccessDict[dimName][1], "Component '%s' doesn't have dimension '%s'." % (componentName, dimName))
      
      dimRepsNeeded = [dimRep for dimRep in availableDimReps if dimRep.name in nonlocalAccessDict and nonlocalAccessDict[dimRep.name][0] != dimRep.name]
      dimRepsNeeded.extend([dimRep for dimRep in availableDimReps if dimRep.name + "_index" in nonlocalAccessDict])
      
      if not dimRepsNeeded:
        replacementString = componentName
      else:
        # Check that the mpi distributed dimension isn't being accessed nonlocally.
        if vector.field.isDistributed:
          for dimRep in dimRepsNeeded:
            if dimRep.hasLocalOffset:
              dimRepName = dimRep.name
              raise CodeParserException(self, nonlocalAccessDict[dimRepName][1],
                                   "It is illegal to access the dimension '%(dimRepName)s' nonlocally because it is being distributed with MPI.\n"
                                   "Try not using MPI or changing the order of your dimensions." % locals())
        
        nonlocalAccessVariableName = '_%s_' % componentName
        nonlocalAccessVariableName += ''.join([dimRep.name for dimRep in dimRepsNeeded])
        
        if not nonlocalAccessVariableName in nonlocalVariablesCreated:
          # Populate with whatever we have set for us if it's there.
          indexOverrides = self.loopArguments.get('indexOverrides', {}).copy()
          for dimRep in dimRepsNeeded:
            indexOverrides[dimRep.name] = {vector.field: dimRep.loopIndex}
          
          argumentsString = ', '.join([dimRep.loopIndex for dimRep in dimRepsNeeded])
          vectorID = vector.id
          componentNumber = vector.components.index(componentName)
          defineString = "#define %(nonlocalAccessVariableName)s(%(argumentsString)s) " % locals()
          
          nonlocalAccessString = "_active_%(vectorID)s[%(componentNumber)s + (0" % locals()
          
          for dimRep in vector.field.inBasis(self.basis):
            termString = self.explicitIndexPointerTermForVectorAndDimRepWithFieldAndBasis(vector, dimRep, self.field, self.basis, indexOverrides)
            nonlocalAccessString += termString.replace('\n', ' \\\n')
          nonlocalAccessString += ') * _%(vectorID)s_ncomponents]' % locals()
          
          defineString += nonlocalAccessString + '\n'
          undefineString = "#undef %(nonlocalAccessVariableName)s\n" % locals()
          
          featureDict = {
            'vector': vector,
            'componentName': componentName,
            'availableDimReps': availableDimReps,
            'dimRepsNeeded': dimRepsNeeded,
            'nonlocalAccessVariableName': nonlocalAccessVariableName,
            'nonlocalAccessString': nonlocalAccessString,
            'defineString': defineString,
            'undefineString': undefineString
          }
          
          featureOrdering = ['Diagnostics']
          
          self.insertCodeForFeatures('nonlocalAccess', featureOrdering, featureDict)
          
          self.prefixCodeString += featureDict['defineString']
          self.postfixCodeString += featureDict['undefineString']
          nonlocalVariablesCreated.add(nonlocalAccessVariableName)
        
        arguments = []
        for dimRep in dimRepsNeeded:
          accessViaIndex = not dimRep.name in nonlocalAccessDict
          dimRepVariableName = dimRep.name if not accessViaIndex else dimRep.name + "_index"
          accessString = nonlocalAccessDict[dimRepVariableName][0]
          dimRepName = dimRep.name
          
          if not accessViaIndex:
            argumentValue = dimRep.nonlocalAccessIndexFromStringForFieldInBasis(accessString, self.field, self.basis)
            if not argumentValue:
              raise CodeParserException(self, nonlocalAccessDict[dimRep.name][1],
                                   "Cannot access the '%(dimRepName)s' dimension nonlocally with the string '%(accessString)s'. Check the documentation." % locals())
          else:
            argumentValue = accessString
          
          arguments.append('/* %(dimRepVariableName)s => %(accessString)s */ (%(argumentValue)s)' % locals())
        argumentsString = ', '.join(arguments)
        replacementString = '%(nonlocalAccessVariableName)s(%(argumentsString)s)' % locals()
      
      # Replace the phi(j => j + 7) string with the appropriate string
      # i.e. _phi_j(j + 7)
      self.codeString = self.codeString[:codeSlice.start] + replacementString + self.codeString[codeSlice.stop:]
    
  
  def transformCodeString(self):
    """Modify the user code as necessary."""
    super(_UserLoopCodeBlock, self).transformCodeString()
    self.fixupNonlocallyAccessedComponents()
    
  
  @callOncePerInstanceGuard
  def bindNamedVectors(self):
    # This function would be called twice otherwise because it gets called specially
    # by the _ScriptElement implementation of bindNamedVectors
    super(_UserLoopCodeBlock, self).bindNamedVectors()
    self.bindNamedVectorsCalled = True
  
  @callOncePerInstanceGuard
  def preflight(self):
    super(_UserLoopCodeBlock, self).preflight()
    
    vectors = set(self.dependencies)
    if self.targetVector:
      vectors.add(self.targetVector)
    
    basis = self.basis
    self.registerVectorsRequiredInBasis(vectors, basis)
    
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
  def loopCodeString(self):
    prefixString = ''.join([cb.prefixCodeString for cb in self.targetCodeBlocks])
    writeLineDirectives = not self.getVar('debug')
    loopStringTemplate = ''
    if writeLineDirectives: loopStringTemplate += '#line %%(lineNumber)i "%s"\n' % self.getVar('scriptName')
    loopStringTemplate += 'target%(targetNum)i = %(codeString)s;\n'
    loopString = ''.join([loopStringTemplate % dict(lineNumber=cb.scriptLineNumber, targetNum=targetNum, codeString=cb.codeString)\
                            for targetNum, cb in enumerate(self.targetCodeBlocks)])
    if writeLineDirectives:
      loopString += '#line _XPDEINT_CORRECT_MISSING_LINE_NUMBER_\n'
    postfixString = ''.join([cb.postfixCodeString for cb in self.targetCodeBlocks])
    return prefixString + loopString + postfixString
  
  def transformCodeString(self):
    # This will be done as needed for all child code blocks
    pass
  
  
  
