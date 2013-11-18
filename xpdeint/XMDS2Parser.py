#!/usr/bin/env python
# encoding: utf-8
"""
XMDS2Parser.py

Created by Graham Dennis on 2007-12-29.

Copyright (c) 2007-2012, Graham Dennis and Joe Hope

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

import re
from xpdeint.ScriptParser import ScriptParser
from xpdeint.ParserException import ParserException, parserWarning
from xpdeint.ParsedEntity import ParsedEntity
from xml.dom import minidom
from xpdeint import RegularExpressionStrings, Utilities

from xpdeint._ScriptElement import _ScriptElement
from xpdeint._UserCodeBlock import _UserCodeBlock
from xpdeint._UserCodeBlock import _UserLoopCodeBlock

from xpdeint.SimulationElement import SimulationElement as SimulationElementTemplate
from xpdeint.Geometry.GeometryElement import GeometryElement as GeometryElementTemplate
from xpdeint.Geometry.FieldElement import FieldElement as FieldElementTemplate
from xpdeint.Geometry._Dimension import _Dimension as Dimension
from xpdeint.Geometry.UniformDimensionRepresentation import UniformDimensionRepresentation
from xpdeint.Geometry.NonUniformDimensionRepresentation import NonUniformDimensionRepresentation

from xpdeint.Vectors.VectorElement import VectorElement as VectorElementTemplate
from xpdeint.Vectors.ComputedVector import ComputedVector as ComputedVectorTemplate
from xpdeint.Vectors.NoiseVector import NoiseVector as NoiseVectorTemplate
from xpdeint.Stochastic.RandomVariables.GaussianBoxMuellerRandomVariable import GaussianBoxMuellerRandomVariable
from xpdeint.Stochastic.RandomVariables.GaussianMKLRandomVariable import GaussianMKLRandomVariable
from xpdeint.Stochastic.RandomVariables.GaussianSolirteRandomVariable import GaussianSolirteRandomVariable
from xpdeint.Stochastic.RandomVariables.UniformRandomVariable import UniformRandomVariable
from xpdeint.Stochastic.RandomVariables.PoissonianRandomVariable import PoissonianRandomVariable
from xpdeint.Stochastic.Generators.POSIXGenerator import POSIXGenerator
from xpdeint.Stochastic.Generators.MKLGenerator import MKLGenerator
from xpdeint.Stochastic.Generators.DSFMTGenerator import DSFMTGenerator
from xpdeint.Stochastic.Generators.SolirteGenerator import SolirteGenerator
from xpdeint.Vectors.VectorInitialisation import VectorInitialisation as VectorInitialisationZeroTemplate
from xpdeint.Vectors.VectorInitialisationFromCDATA import VectorInitialisationFromCDATA as VectorInitialisationFromCDATATemplate
from xpdeint.Vectors.VectorInitialisationFromXSIL import VectorInitialisationFromXSIL as VectorInitialisationFromXSILTemplate
from xpdeint.Vectors.VectorInitialisationFromHDF5 import VectorInitialisationFromHDF5 as VectorInitialisationFromHDF5Template


from xpdeint.Segments.TopLevelSequenceElement import TopLevelSequenceElement as TopLevelSequenceElementTemplate
from xpdeint.SimulationDrivers.SimulationDriver import SimulationDriver as SimulationDriverTemplate
from xpdeint.SimulationDrivers.MultiPathDriver import MultiPathDriver as MultiPathDriverTemplate
from xpdeint.SimulationDrivers.MPIMultiPathDriver import MPIMultiPathDriver as MPIMultiPathDriverTemplate
from xpdeint.SimulationDrivers.AdaptiveMPIMultiPathDriver import AdaptiveMPIMultiPathDriver as AdaptiveMPIMultiPathDriverTemplate
from xpdeint.SimulationDrivers.DistributedMPIDriver import DistributedMPIDriver as DistributedMPIDriverTemplate

from xpdeint.Segments import Integrators
from xpdeint.Segments.FilterSegment import FilterSegment as FilterSegmentTemplate
from xpdeint.Segments.BreakpointSegment import BreakpointSegment as BreakpointSegmentTemplate
from xpdeint.Segments.SequenceSegment import SequenceSegment as SequenceSegmentTemplate

from xpdeint.Operators.OperatorContainer import OperatorContainer as OperatorContainerTemplate

from xpdeint.Operators.DeltaAOperator import DeltaAOperator as DeltaAOperatorTemplate
from xpdeint.Operators.ConstantIPOperator import ConstantIPOperator as ConstantIPOperatorTemplate
from xpdeint.Operators.NonConstantIPOperator import NonConstantIPOperator as NonConstantIPOperatorTemplate
from xpdeint.Operators.ConstantEXOperator import ConstantEXOperator as ConstantEXOperatorTemplate
from xpdeint.Operators.NonConstantEXOperator import NonConstantEXOperator as NonConstantEXOperatorTemplate
from xpdeint.Operators.FilterOperator import FilterOperator as FilterOperatorTemplate
from xpdeint.Operators.CrossPropagationOperator import CrossPropagationOperator as CrossPropagationOperatorTemplate
from xpdeint.Operators.FunctionsOperator import FunctionsOperator as FunctionsOperatorTemplate


from xpdeint.MomentGroupElement import MomentGroupElement as MomentGroupTemplate

from xpdeint import Features

from xpdeint.Features import Transforms

# TODO: Must check that we are never sampling a temporary vector when it doesn't exist.
# The way to do this is after the template tree has been built to iterate over all elements that can sample
# and verifying that it isn't sampling a temporary vector that it didn't create (or is a child of the creator).


class XMDS2Parser(ScriptParser):
  @staticmethod
  def canParseXMLDocument(xmlDocument):
    simulationElement = xmlDocument.getChildElementByTagName("simulation")
    if not simulationElement.hasAttribute('xmds-version') or simulationElement.getAttribute('xmds-version') != '2':
      return False
    return True
  
  def domainPairFromString(self, domainString, element):
    """
    Parse a string of the form ``(someNumber1, someNumber2)`` and return the two
    strings corresponding to the numbers ``someNumber1`` and ``someNumber2`` 
    """
    
    regex = re.compile(RegularExpressionStrings.domainPair)
    result = regex.match(domainString)
    if not result:
      raise ParserException(element, "Could not understand '%(domainString)s' as a domain"
                                     " of the form ( +/-someNumber, +/-someNumber)" % locals())
    
    minimumString = result.group(1)
    maximumString = result.group(2)
    
    return minimumString, maximumString
  
  def parseXMLDocument(self, xmlDocument, globalNameSpace, filterClass):
    self.argumentsToTemplateConstructors = {'searchList':[globalNameSpace], 'filter': filterClass}
    self.globalNameSpace = globalNameSpace
    
    _ScriptElement.argumentsToTemplateConstructors = self.argumentsToTemplateConstructors
    
    simulationElement = xmlDocument.getChildElementByTagName("simulation")
    
    nameElement = simulationElement.getChildElementByTagName('name', optional=True)
    if nameElement:
        self.globalNameSpace['simulationName'] = nameElement.innerText()
    
    authorElement = simulationElement.getChildElementByTagName('author', optional=True)
    if authorElement: author = authorElement.innerText()
    else: author = ''
    self.globalNameSpace['author'] = author
    
    
    descriptionElement = simulationElement.getChildElementByTagName('description', optional=True)
    if descriptionElement: description = descriptionElement.innerText()
    else: description = ''
    self.globalNameSpace['simulationDescription'] = description
    
    self.simulation = _ScriptElement.simulation
    
    simulationElementTemplate = SimulationElementTemplate(parent = self.simulation, **self.argumentsToTemplateConstructors)
    
    self.parseFeatures(simulationElement)
    
    self.parseDriverElement(simulationElement)
    
    self.parseGeometryElement(simulationElement)
    
    self.parseVectorElements(simulationElement)
    
    self.parseComputedVectorElements(simulationElement, None)
    
    self.parseNoiseVectorElements(simulationElement, None)
    
    self.parseTopLevelSequenceElement(simulationElement)
    
    self.parseOutputElement(simulationElement)
    
  
  def parseDependencies(self, element, optional = False):
    dependenciesElement = element.getChildElementByTagName('dependencies', optional)
    dependencyVectorNames = []
    if dependenciesElement:
      dependencyVectorNames = Utilities.symbolsInString(dependenciesElement.innerText(), xmlElement = element)
      return ParsedEntity(dependenciesElement, dependencyVectorNames)
    else:
      return None
    
  
  def parseDriverElement(self, simulationElement):
    driverClass = SimulationDriverTemplate
    
    driverAttributeDictionary = dict()
    
    driverElement = simulationElement.getChildElementByTagName('driver', optional=True)
    if driverElement:
      
      driverName = driverElement.getAttribute('name').strip().lower()
      
      class UnknownDriverException(Exception):
        pass

      # Check to see if run-time validation has been selected
      runTimeValidationSelected = False
      validationFeature = None
      if 'Validation' in self.globalNameSpace['features']:
        validationFeature = self.globalNameSpace['features']['Validation']
        if validationFeature.runValidationChecks == True:
          runTimeValidationSelected = True
        
      try:
        if 'multi-path' in driverName:
          if driverName == 'multi-path':
            driverClass = MultiPathDriverTemplate
          elif driverName == 'mpi-multi-path':
            driverClass = MPIMultiPathDriverTemplate
          elif driverName == 'adaptive-mpi-multi-path':
            driverClass = AdaptiveMPIMultiPathDriverTemplate
          else:
            raise UnknownDriverException()
          
          if not driverElement.hasAttribute('paths'):
            raise ParserException(driverElement, "Missing 'paths' attribute for multi-path driver.")

          pathCountString = driverElement.getAttribute('paths')
          try:
            pathCount = RegularExpressionStrings.integerInString(pathCountString)
          except ValueError, err:
            # If we didn't parse it, then we might be using the run-time validation feature
            if runTimeValidationSelected:
              validationFeature.validationChecks.append("""
              if (%(pathCountString)s <= 0)
                _LOG(_ERROR_LOG_LEVEL, "ERROR: The number of paths '%(pathCountString)s' must be greater than zero.\\n"
                                       "pathCount = %%li\\n", (long)%(pathCountString)s);
              """ % locals())
              pathCount = pathCountString
            else:
              raise ParserException(driverElement, "Could not understand path count '%(pathCountString)s' as an integer. "
                                                   """Use feature <validation kind="run-time"/> to allow arbitrary code.""")
          driverAttributeDictionary['pathCount'] = pathCount
        elif driverName == 'none':
          pass
        elif driverName == 'distributed-mpi':
          driverClass = DistributedMPIDriverTemplate
        else:
          raise UnknownDriverException()
      except UnknownDriverException, err:
        raise ParserException(driverElement, "Unknown driver type '%(driverName)s'. "
                                             "The options are 'none' (default), 'multi-path', 'mpi-multi-path', 'adaptive-mpi-multi-path' or 'distributed-mpi'." % locals())
      
      if driverClass == MultiPathDriverTemplate:
        kindString = None
        if driverElement.hasAttribute('kind'):
          kindString = driverElement.getAttribute('kind').strip().lower()
        if kindString in (None, 'single'):
          pass
        elif kindString == 'mpi':
          driverClass = MPIMultiPathDriverTemplate
        else:
          raise ParserException(driverElement,
                                "Unknown multi-path kind '%(kindString)s'. "
                                "The options are 'single' (default), or 'mpi'." % locals())
    
    simulationDriver = driverClass(parent = self.simulation, xmlElement = driverElement,
                                   **self.argumentsToTemplateConstructors)
    self.applyAttributeDictionaryToObject(driverAttributeDictionary, simulationDriver)
    return simulationDriver
  
  
  def parseFeatures(self, simulationElement):
    featuresParentElement = simulationElement.getChildElementByTagName('features', optional=True)
    if not featuresParentElement:
      featuresParentElement = simulationElement
    
    transformMultiplexer = Transforms.TransformMultiplexer.TransformMultiplexer(parent = self.simulation,
                                                                                **self.argumentsToTemplateConstructors)
    
    def parseSimpleFeature(tagName, featureClass):
      featureElement = featuresParentElement.getChildElementByTagName(tagName, optional=True)
      feature = None
      if featureElement:
        if len(featureElement.innerText()) == 0 or featureElement.innerText().lower() == 'yes':
          feature = featureClass(parent = self.simulation, xmlElement = featureElement,
                                 **self.argumentsToTemplateConstructors)
      return featureElement, feature
    
    
    parseSimpleFeature('auto_vectorise', Features.AutoVectorise.AutoVectorise)
    parseSimpleFeature('benchmark', Features.Benchmark.Benchmark)
    parseSimpleFeature('error_check', Features.ErrorCheck.ErrorCheck)
    parseSimpleFeature('bing', Features.Bing.Bing)
    parseSimpleFeature('openmp', Features.OpenMP.OpenMP)
    parseSimpleFeature('halt_non_finite', Features.HaltNonFinite.HaltNonFinite)
    parseSimpleFeature('diagnostics', Features.Diagnostics.Diagnostics)
    
    openmpElement = featuresParentElement.getChildElementByTagName('openmp', optional=True)
    if openmpElement:
      threadCount = None
      if openmpElement.hasAttribute('threads'):
        try:
          threadCountString = openmpElement.getAttribute('threads')
          threadCount = int(threadCountString)
        except ValueError, err:
          raise ParserException(openmpElement, "Cannot understand '%(threadCountString)s' as an "
                                               "integer number of threads." % locals())
        
        if threadCount <= 0:
          raise ParserException(openmpElement, "The number of threads must be greater than 0.")
      openmpFeature = Features.OpenMP.OpenMP(parent = self.simulation,
                                             xmlElement = openmpElement,
                                             **self.argumentsToTemplateConstructors)
      openmpFeature.threadCount = threadCount
    
    precisionElement = featuresParentElement.getChildElementByTagName('precision', optional=True)
    if precisionElement:
      content = precisionElement.innerText().strip().lower()
      if content:
        if not content in ['single', 'double']:
          raise ParserException(
            precisionElement,
            "Unrecognised precision '%s'. Options are 'single' or 'double' (default)." % content
          )
        self.globalNameSpace['precision'] = content
    
    chunkedOutputElement = featuresParentElement.getChildElementByTagName('chunked_output', optional=True)
    if chunkedOutputElement:
      sizeString = chunkedOutputElement.getAttribute('size').strip().lower()
      match = re.match(r'(\d+)(b|kb|mb|gb|tb)', sizeString)
      if not match:
        raise ParserException(
          chunkedOutputElement,
          "The 'size' attribute of the 'chunked_output' tag must be an integer followed by one of the suffixes "
          "'B' (bytes), 'kB' (kilobytes), 'MB' (megabytes), 'GB' (gigabytes) or 'TB' (terabytes)."
        )
      chunkSize = int(match.group(1))
      chunkSize *= 1024 ** {'b': 0, 'kb': 1, 'mb': 2, 'gb': 3, 'tb': 4}[match.group(2)]
      chunkedOutputFeature = Features.ChunkedOutput.ChunkedOutput(
        parent = self.simulation,
        chunkSize = chunkSize,
        xmlElement = chunkedOutputElement,
        **self.argumentsToTemplateConstructors
      )

    validationFeatureElement = featuresParentElement.getChildElementByTagName('validation', optional=True)
    if validationFeatureElement and validationFeatureElement.hasAttribute('kind'):
      kindString = validationFeatureElement.getAttribute('kind').strip().lower()
      
      if kindString in ('run-time', 'none'):
        validationFeature = Features.Validation.Validation(
          parent = self.simulation,
          runValidationChecks = kindString == 'run-time',
          xmlElement = validationFeatureElement,
          **self.argumentsToTemplateConstructors
        )
      elif kindString == 'compile-time':
        pass
      else:
        raise ParserException(validationFeatureElement, "The 'kind' attribute of the <validation> tag must be one of "
                                                        "'compile-time', 'run-time' or 'none'.")
      
    # We want the Globals element to be parsed before the Arguments element so that the globals for globals
    # appear in the generated source before the globals for Arguments.  This prevents anyone inadvertently using
    # the arguments in the initialisation of the globals.  To achieve this, people should put code in the CDATA
    # block for arguments.
    
    globalsElement = featuresParentElement.getChildElementByTagName('globals', optional=True)
    if globalsElement:
      globalsTemplate = Features.Globals.Globals(parent = self.simulation,
                                                 **self.argumentsToTemplateConstructors)
      globalsTemplate.codeBlocks['globalsCode'] = _UserCodeBlock(
        parent = globalsTemplate, xmlElement = globalsElement,
        **self.argumentsToTemplateConstructors
      )

    argumentsFeatureElement = featuresParentElement.getChildElementByTagName('arguments', optional=True)
    
    if argumentsFeatureElement:
      argumentsFeature = Features.Arguments.Arguments(
        parent = self.simulation, xmlElement = argumentsFeatureElement,
        **self.argumentsToTemplateConstructors
      )
      
      argumentElements = argumentsFeatureElement.getChildElementsByTagName('argument', optional=True)
      
      if argumentsFeatureElement.getAttribute('append_args_to_output_filename') == "yes":
        argumentsFeature.appendArgsToOutputFilename = True
      else:
        argumentsFeature.appendArgsToOutputFilename = False

      argumentsFeature.codeBlocks['postArgumentProcessing'] = _UserCodeBlock(
        xmlElement = argumentsFeatureElement, parent = argumentsFeature,
        **self.argumentsToTemplateConstructors
      )
      
      argumentList = []
      # Note that "h" is already taken as the "help" option 
      shortOptionNames = set(['h'])
      
      for argumentElement in argumentElements:
        name = argumentElement.getAttribute('name').strip()
        type = argumentElement.getAttribute('type').strip().lower()
        defaultValue = argumentElement.getAttribute('default_value').strip()
        
        # Determine the short name (i.e. single character) of the full option name
        shortName = ""
        additionalAllowedCharacters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        for character in name+additionalAllowedCharacters:
          if character not in shortOptionNames:
            shortName = character
            shortOptionNames.add(character)
            break
        
        if shortName == "":
          raise ParserException(argumentElement, "Unable to find a short (single character) name for command line option")        
        
        if not type in ('int', 'integer', 'long', 'real', 'string'):
          raise ParserException(argumentElement, "Invalid type name '%(type)s'. "
                                                 "Valid options are 'integer', 'int', 'long', 'real' or 'string'." % locals())
        
        argumentAttributeDictionary = dict()
        
        argumentAttributeDictionary['name'] = name
        argumentAttributeDictionary['shortName'] = shortName
        argumentAttributeDictionary['type'] = type
        argumentAttributeDictionary['defaultValue'] = defaultValue
        
        argumentList.append(argumentAttributeDictionary)
      
      argumentsFeature.argumentList = argumentList
    
    

    
    cflagsElement = featuresParentElement.getChildElementByTagName('cflags', optional=True)
    if cflagsElement:
      cflagsTemplate = Features.CFlags.CFlags(parent = self.simulation,
                                              **self.argumentsToTemplateConstructors)
      cflagsTemplate.cflagsString = cflagsElement.innerText().strip()
    
    fftwElement = featuresParentElement.getChildElementByTagName('fftw', optional=True)
    
    if fftwElement:
      fourierTransformClass = Transforms.FourierTransformFFTW3.FourierTransformFFTW3
      fftAttributeDictionary = dict()
      
      threadCount = 1
      if fftwElement.hasAttribute('threads'):
        try:
          threadCountString = fftwElement.getAttribute('threads')
          threadCount = int(threadCountString)
        except ValueError, err:
          raise ParserException(fftwElement, "Cannot understand '%(threadCountString)s' as an "
                                             "integer number of threads." % locals())
        
        if threadCount <= 0:
          raise ParserException(fftwElement, "The number of threads must be greater than 0.")
      
      planType = None
      if not fftwElement.hasAttribute('plan'):
        pass
      else:
        planType = {
          'estimate': 'FFTW_ESTIMATE',
          'measure': 'FFTW_MEASURE',
          'patient': 'FFTW_PATIENT',
          'exhaustive': 'FFTW_EXHAUSTIVE'
        }.get(fftwElement.getAttribute('plan').strip().lower())
        if not planType:
          raise ParserException(fftwElement, "The plan attribute must be one of 'estimate', 'measure', 'patient' or 'exhaustive'.")
      
      if planType:
        fftAttributeDictionary['planType'] = planType
      
      
      if 'OpenMP' in self.globalNameSpace['features'] or threadCount > 1:
        if fourierTransformClass == Transforms.FourierTransformFFTW3.FourierTransformFFTW3:
          fourierTransformClass = Transforms.FourierTransformFFTW3Threads.FourierTransformFFTW3Threads
          if 'OpenMP' in self.globalNameSpace['features']:
            fourierTransformClass.fftwSuffix = 'omp'
            threadCount = 'omp_get_max_threads()'
        elif fourierTransformClass == Transforms._NoTransform._NoTransform:
          raise ParserException(fftwElement, "Can't use threads with no fourier transforms.")
        else:
          # This shouldn't be reached because the fourierTransformClass should be one of the above options
          raise ParserException(fftwElement, "Internal consistency error.")
        
        fftAttributeDictionary['threadCount'] = threadCount
      
      fourierTransform = fourierTransformClass(parent = self.simulation, **self.argumentsToTemplateConstructors)
      
      self.applyAttributeDictionaryToObject(fftAttributeDictionary, fourierTransform)
  
  def parseFeatureAttributes(self, someElement, someTemplate):
    self.parseMaxIterationsAttribute(someElement, someTemplate)
  
  def parseMaxIterationsAttribute(self, someElement, someTemplate):
    if not isinstance(someTemplate, Integrators.AdaptiveStep.AdaptiveStep):
      return
    
    if not someElement.hasAttribute('max_iterations'):
      return
    
    maxIterationsString = someElement.getAttribute('max_iterations').strip()
    try:
      maxIterations = int(maxIterationsString)
      if not maxIterations >= 1:
        raise ParserException(someElement, "max_iterations value must be a positive integer.")
    except ValueError, err:
      raise ParserException(someElement, "Unable to understand '%(maxIterationsString)s' as an integer for 'max_iterations'.")
    
    if not 'MaxIterations' in self.globalNameSpace['features']:
      maxIterationsFeature = Features.MaxIterations.MaxIterations(**self.argumentsToTemplateConstructors)
      maxIterationsFeature.maxIterationsDict = {}
    else:
      maxIterationsFeature = self.globalNameSpace['features']['MaxIterations']
    
    maxIterationsFeature.maxIterationsDict[someTemplate] = maxIterations
  
  def parseGeometryElement(self, simulationElement):
    geometryElement = simulationElement.getChildElementByTagName('geometry')
    
    geometryTemplate = GeometryElementTemplate(parent = self.simulation, **self.argumentsToTemplateConstructors)
    
    ## First grab the propagation dimension name
    
    propagationDimensionElement = geometryElement.getChildElementByTagName('propagation_dimension')
    if len(propagationDimensionElement.innerText()) == 0:
      raise ParserException(propagationDimensionElement, "The propagation_dimension element must not be empty")
    
    propagationDimensionName = propagationDimensionElement.innerText()
    self.globalNameSpace['globalPropagationDimension'] = propagationDimensionName
    self.globalNameSpace['symbolNames'].add(propagationDimensionName)
    
    noTransform = self.globalNameSpace['features']['TransformMultiplexer'].transformWithName('none')
    
    propagationDimension = Dimension(name = propagationDimensionName,
                                     transverse = False,
                                     transform = noTransform,
                                     parent = geometryTemplate,
                                     **self.argumentsToTemplateConstructors)
    
    propagationDimension.addRepresentation(
      NonUniformDimensionRepresentation(
        name = propagationDimensionName,
        type = 'real',
        parent = propagationDimension,
        xmlElement = propagationDimensionElement,
        tag = NonUniformDimensionRepresentation.tagForName('coordinate'),
        **self.argumentsToTemplateConstructors
      )
    )
    
    geometryTemplate.dimensions = [propagationDimension]
    
    ## Now grab and parse all of the transverse dimensions
    
    geometryTemplate.primaryTransverseDimensionNames = []
    
    transverseDimensionsElement = geometryElement.getChildElementByTagName('transverse_dimensions', optional=True)
    if transverseDimensionsElement:
      dimensionElements = transverseDimensionsElement.getChildElementsByTagName('dimension', optional=True)
      
      aliasDimensions = []
      
      for dimensionElement in dimensionElements:
        def parseAttribute(attrName):
          if not dimensionElement.hasAttribute(attrName) or len(dimensionElement.getAttribute(attrName)) == 0:
            raise ParserException(dimensionElement, "Each dimension element must have a non-empty"
                                                    " '%(attrName)s' attribute" % locals())
          
          return dimensionElement.getAttribute(attrName).strip()
        
        
        ## Grab the name of the dimension
        dimensionName = parseAttribute('name')
        
        try:
          dimensionName = Utilities.symbolInString(dimensionName, xmlElement = dimensionElement)
        except ValueError, err:
          raise ParserException(dimensionElement, "'%(dimensionName)s is not a valid name for a dimension.\n"
                                                  "It must not start with a number, and can only contain "
                                                  "alphanumeric characters and underscores." % locals())
        ## Make sure the name is unique
        if dimensionName in self.globalNameSpace['symbolNames']:
          raise ParserException(dimensionElement, "Dimension name %(dimensionName)s conflicts with "
                                                  "previously-defined symbol of the same name." % locals())
        
        geometryTemplate.primaryTransverseDimensionNames.append(dimensionName)
        
        ## Now make sure no-one else steals it
        self.globalNameSpace['symbolNames'].add(dimensionName)
        
        # Work out the type of the dimension
        dimensionType = 'real'
        if dimensionElement.hasAttribute('type') and dimensionElement.getAttribute('type'):
          dimensionType = dimensionElement.getAttribute('type').strip().lower()
          if dimensionType == 'real':
            pass
          elif dimensionType in ('long', 'int', 'integer'):
            dimensionType = 'long'
          else:
            raise ParserException(dimensionElement, "'%(dimensionType)s' is not a valid type for a dimension.\n"
                                                    "It must be one of 'real' (default) or "
                                                    "'integer'/'int'/'long' (synonyms)." % locals())
        
        
        transform = None
        transformName = 'none'
        transformMultiplexer = self.globalNameSpace['features']['TransformMultiplexer']
        
        if dimensionType == 'real' and dimensionElement.hasAttribute('transform'):
          transformName = dimensionElement.getAttribute('transform').strip()
          transform = transformMultiplexer.transformWithName(transformName.lower())
          if not transform:
            raise ParserException(dimensionElement, "Unknown transform of type '%(transformName)s'." % locals())
        
        if dimensionType == 'long':
          transform = transformMultiplexer.transformWithName('none')
        
        if not transform:
          # default to 'dft'
          # FIXME: This is debatable. Perhaps a default of 'none' is more sensible.
          transformName = 'dft'
          transform = transformMultiplexer.transformWithName('dft')


        if dimensionElement.hasAttribute('domain'):
          ## Grab the domain strings
          
          domainString = parseAttribute('domain')
          
          ## Returns two strings for the end points
          minimumString, maximumString = self.domainPairFromString(domainString, dimensionElement)
        elif dimensionElement.hasAttribute('length_scale'):
          minimumString = '0'
          maximumString = dimensionElement.getAttribute('length_scale').strip()
        else:
          raise ParserException(dimensionElement, "Each dimension element must have a non-empty 'domain' attribute\n"
                                                  "(or in the case of the 'hermite-gauss' transform a 'length_scale' attribute).")

        # Check to see if run-time validation has been selected
        runTimeValidationSelected = False
        validationFeature = None
        if 'Validation' in self.globalNameSpace['features']:
          validationFeature = self.globalNameSpace['features']['Validation']
          if validationFeature.runValidationChecks == True:
            runTimeValidationSelected = True
        
        if dimensionType == 'real':
          domainPairType = float
        else:
          domainPairType = int
        ## Now we try make some sense of them
        try:
          minimumValue = domainPairType(minimumString)
          maximumValue = domainPairType(maximumString)
        except ValueError, err: # If not floats then we check the validation feature.
          if runTimeValidationSelected:
            validationFeature.validationChecks.append("""
            if (%(minimumString)s >= %(maximumString)s)
              _LOG(_ERROR_LOG_LEVEL, "ERROR: The end point of the dimension '%(maximumString)s' must be "
                                     "greater than the start point.\\n"
                                     "Start = %%e, End = %%e\\n", (real)%(minimumString)s, (real)%(maximumString)s);""" % locals())
          else:
            raise ParserException(dimensionElement, """Could not understand domain (%(minimumString)s, %(maximumString)s) as numbers.
Use feature <validation kind="run-time"/> to allow for arbitrary code.""" % locals() )
        else: # In this case we were given numbers and should check that they in the correct order here
          if minimumValue >= maximumValue:
            raise ParserException(dimensionElement, "The end point of the dimension, '%(maximumString)s', must be "
                                                    "greater than the start point, '%(minimumString)s'." % locals())
        

        if dimensionType == 'real' or dimensionElement.hasAttribute('lattice'):
          ## Grab the number of lattice points and make sure it's a positive integer
          latticeString = parseAttribute('lattice')
          if not latticeString.isdigit():
            # This might be okay if the user has asked for run-time validation, so that
            # the lattice value is actually a variable to be specified later.

            # Real dimension, lattice attribute isn't a number, so is run-time validation on?
            if runTimeValidationSelected == False:
              # Not on, so barf
              raise ParserException(dimensionElement, "Could not understand lattice value "
                                                    "'%(latticeString)s' as a positive integer. "
                                                    "If you want to specify the lattice value at runtime you need "
                                                    "to add <validation kind=\"run-time\"/> to your features block."  % locals())

            # For now only allow run-time lattice definition for 'none', 'dft', 'dct' and 'dst' transforms.
            # This is because lattice points for Hermite-Gauss and Bessel transforms are not uniformly spaced,
            # and currently the spacing is worked out in _MMT.py at parse time, which requires the number
            # of lattice points to be known.            
            if transformName not in ['dft', 'dct', 'dst', 'none']:
              raise ParserException(dimensionElement, "Defining the lattice size at run time is currently only "
                                                      "implemented for transform types 'dft', 'dct', 'dst' and 'none'. "
                                                      "You are using transform type '%(transformName)s'. Aborting." % locals())

            # All right, we have real dimension, run-time validation is on, an acceptable tranform is in
            # use, so let's allow a non-numeric lattice value
            lattice = latticeString
          else:
            # The lattice string a digit, so everything is cool
            lattice = int(latticeString)
            if dimensionType == 'long' and (not runTimeValidationSelected) and (maximumValue - minimumValue + 1) != lattice:
              raise ParserException(dimensionElement, "The lattice value of '%(latticeString)s' doesn't match with the domain "
                                                    "'%(domainString)s'." % locals())
          
          # If we are validating at run time, an explicit lattice has been provided, and we are a long dimension then we need to check that the lattice
          # agrees with the minimum / maximum values of the dimension.
          if runTimeValidationSelected and dimensionType == 'long':
            validationFeature.validationChecks.append("""
            if ((%(latticeString)s) != ((%(maximumString)s) - (%(minimumString)s) + 1))
              _LOG(_ERROR_LOG_LEVEL, "ERROR: The lattice value of '%(latticeString)s'=%%li doesn't match with the domain "
                                     "'%(minimumString)s'=%%li to '%(maximumString)s'=%%li (%%li lattice points).\\n",
                                     long(%(latticeString)s), long(%(minimumString)s), long(%(maximumString)s), long((%(maximumString)s) - (%(minimumString)s)+1));
            """ % locals())
        else:
          # Only for 'long' dimensions
          if not runTimeValidationSelected:
            lattice = maximumValue - minimumValue + 1
          else:
            lattice = "((%(maximumString)s) - (%(minimumString)s) + 1)" % locals()
        
        
        aliasNames = []
        if dimensionElement.hasAttribute('aliases'):
          aliasNames.extend(Utilities.symbolsInString(dimensionElement.getAttribute('aliases'), xmlElement = dimensionElement))
          for aliasName in aliasNames:
            if aliasName in self.globalNameSpace['symbolNames']:
              raise ParserException(dimensionElement, "Cannot use '%(aliasName)s' as an alias name for dimension '%(dimensionName)s\n"
                                                      "This name is already in use." % locals())
            self.globalNameSpace['symbolNames'].add(aliasName)
        
        aliasNames.insert(0, dimensionName)
        
        if dimensionElement.hasAttribute('spectral_lattice'):
          spectralLattice = dimensionElement.getAttribute('spectral_lattice').strip()
          if not spectralLattice.isdigit():
            raise ParserException(dimensionElement, "Could not understand spectral_lattice value of '%(spectralLattice)s' as a positive integer." % locals())
          spectralLattice = int(spectralLattice)
          if spectralLattice > lattice:
            raise ParserException(dimensionElement, "The size of the spectral lattice must be equal or less than the size of the spatial lattice.")
        else:
          spectralLattice = lattice
        
        volumePrefactor = None
        if dimensionElement.hasAttribute('volume_prefactor'):
            volumePrefactor = dimensionElement.getAttribute('volume_prefactor').strip()
        
        aliasNameSet = set(aliasNames)
        
        for aliasName in aliasNames:
          dim = transform.newDimension(name = aliasName, lattice = lattice,
                                       spectralLattice = spectralLattice, type = dimensionType,
                                       minimum = minimumString, maximum = maximumString,
                                       parent = geometryTemplate, transformName = transformName,
                                       aliases = aliasNameSet, volumePrefactor = volumePrefactor,
                                       xmlElement = dimensionElement)
          if aliasName == dimensionName:
            geometryTemplate.dimensions.append(dim)
          else:
            aliasDimensions.append(dim)
      
      # Alias dimensions come after normal dimensions so that we don't end up with a distributed-mpi set up over the first dimension and its alias
      geometryTemplate.dimensions.extend(aliasDimensions)
    
    driver = self.globalNameSpace['features']['Driver']
    if isinstance(driver, DistributedMPIDriverTemplate):
      transverseDimensions = geometryTemplate.dimensions[1:]
      mpiTransform = transverseDimensions[0].transform
      if not mpiTransform.isMPICapable:
        mpiTransform = transformMultiplexer.transformWithName('mpi')
      mpiTransform.initialiseForMPIWithDimensions(transverseDimensions)
    
    return geometryTemplate
  
  def parseVectorElements(self, parentElement):
    vectorElements = parentElement.getChildElementsByTagName('vector', optional=True)
    for vectorElement in vectorElements:
      vectorTemplate = self.parseVectorElement(vectorElement)
  
  def parseVectorElement(self, vectorElement):
    if not vectorElement.hasAttribute('dimensions'):
      dimensionNames = self.globalNameSpace['geometry'].primaryTransverseDimensionNames
    elif len(vectorElement.getAttribute('dimensions').strip()) == 0:
      # No dimensions
      dimensionNames = []
    else:
      dimensionsString = vectorElement.getAttribute('dimensions').strip()
      dimensionNames = Utilities.symbolsInString(dimensionsString, xmlElement = vectorElement)
      if not dimensionNames:
        raise ParserException(vectorElement, "Cannot understand '%(dimensionsString)s' as a "
                                            "list of dimensions" % locals())
        
    
    fieldTemplate = FieldElementTemplate.sortedFieldWithDimensionNames(dimensionNames, xmlElement = vectorElement)
    
    if not vectorElement.hasAttribute('name') or len(vectorElement.getAttribute('name')) == 0:
      raise ParserException(vectorElement, "Each vector element must have a non-empty 'name' attribute")
    
    vectorName = vectorElement.getAttribute('name')
    if not vectorName == Utilities.symbolInString(vectorName, xmlElement = vectorElement):
      raise ParserException(vectorElement, "'%(vectorName)s' is not a valid name for a vector.\n"
                                           "The name must not start with a number and can only contain letters, numbers and underscores." % locals())
    
    # Check that this vector name is unique
    for field in self.globalNameSpace['fields']:
      if len(filter(lambda x: x.name == vectorName, field.vectors)) > 0:
        raise ParserException(vectorElement, "Vector name '%(vectorName)s' conflicts with a "
                                             "previously defined vector of the same name" % locals())
    
    ## Check that the name isn't already taken
    if vectorName in self.globalNameSpace['symbolNames']:
      raise ParserException(vectorElement, "Vector name '%(vectorName)s' conflicts with previously "
                                          "defined symbol of the same name." % locals())
    
    ## Make sure no-one else takes the name
    self.globalNameSpace['symbolNames'].add(vectorName)
    
    # Backwards compatibility
    if vectorElement.hasAttribute('initial_space'):
      basis_string = vectorElement.getAttribute('initial_space')
      vectorElement.setAttribute('initial_basis', basis_string)
    
    if vectorElement.hasAttribute('initial_basis'):
      initialBasis = fieldTemplate.basisFromString(
        vectorElement.getAttribute('initial_basis'),
        xmlElement = vectorElement
      )
    else:
      initialBasis = fieldTemplate.defaultCoordinateBasis
    
    typeString = None
    if vectorElement.hasAttribute('type'):
      typeString = vectorElement.getAttribute('type').lower()
    
    if typeString in (None, 'complex'):
      typeString = 'complex'
    elif typeString == 'real':
      typeString = 'real'
    else:
      raise ParserException(
        vectorElement,
        "Unknown type '%(typeString)s'. "
        "Options are 'complex' (default), or 'real'" % locals()
      )
    
    vectorTemplate = VectorElementTemplate(
      name = vectorName, field = fieldTemplate, initialBasis = initialBasis,
      type = typeString, xmlElement = vectorElement,
      **self.argumentsToTemplateConstructors
    )
    
    self.globalNameSpace['simulationVectors'].append(vectorTemplate)
    
    componentsElement = vectorElement.getChildElementByTagName('components')
    
    componentsString = componentsElement.innerText()
    if not componentsString:
      raise ParserException(componentsElement, "The components element must not be empty")
    
    results = Utilities.symbolsInString(componentsString, componentsElement)
    
    if not results:
      raise ParserException(componentsElement, "Could not extract component names from component string "
                                               "'%(componentsString)s'." % locals())
    
    for componentName in results:
      if componentName in self.globalNameSpace['symbolNames']:
        raise ParserException(componentsElement, "Component name '%(componentName)s' conflicts with "
                                                 "a previously-defined symbol of the same name." % locals())
      self.globalNameSpace['symbolNames'].add(componentName)
      
      vectorTemplate.components.append(componentName)
    
    initialisationElement = vectorElement.getChildElementByTagName('initialisation', optional=True)
    
    if initialisationElement:
      initialisationTemplate = vectorTemplate.initialiser
      kindString = None
      if initialisationElement.hasAttribute('kind'):
        kindString = initialisationElement.getAttribute('kind').lower()
      
      def createInitialisationCodeBlock():
        initialisationCodeBlock = _UserLoopCodeBlock(
          field = vectorTemplate.field, xmlElement = initialisationElement,
          basis = vectorTemplate.initialBasis, parent = initialisationTemplate,
          **self.argumentsToTemplateConstructors)
        initialisationCodeBlock.dependenciesEntity = self.parseDependencies(initialisationElement, optional=True)
        initialisationCodeBlock.targetVector = vectorTemplate
        return initialisationCodeBlock
      
      
      if kindString in (None, 'code'):
        initialisationTemplate = VectorInitialisationFromCDATATemplate(parent = vectorTemplate, xmlElement=initialisationElement,
                                                                       **self.argumentsToTemplateConstructors)
        initialisationCodeBlock = createInitialisationCodeBlock()
        initialisationTemplate.codeBlocks['initialisation'] = initialisationCodeBlock
        
        if len(initialisationCodeBlock.codeString) == 0:
          raise ParserException(initialisationElement, "Empty initialisation code in 'code' initialisation element.")
      elif kindString == 'zero':
        initialisationTemplate = vectorTemplate.initialiser
      elif kindString in ['xsil', 'hdf5']:
        if kindString == 'xsil':
          initialisationTemplateClass = VectorInitialisationFromXSILTemplate
        elif kindString == 'hdf5':
          initialisationTemplateClass = VectorInitialisationFromHDF5Template
        initialisationTemplate = initialisationTemplateClass(parent = vectorTemplate, xmlElement=initialisationElement,
                                                             **self.argumentsToTemplateConstructors)
        geometryMatchingMode = 'strict'
        if initialisationElement.hasAttribute('geometry_matching_mode'):
          geometryMatchingMode = initialisationElement.getAttribute('geometry_matching_mode').strip().lower()
          if not geometryMatchingMode in ('strict', 'loose'):
            raise ParserException(initialisationElement, "The geometry matching mode for XSIL/HDF5 import must either be 'strict' or 'loose'.")
        initialisationTemplate.geometryMatchingMode = geometryMatchingMode
        
        filenameElement = initialisationElement.getChildElementByTagName('filename')

        if kindString == 'xsil':
          momentGroupName = 'NULL'
          if filenameElement.hasAttribute('group'):
            momentGroupName = 'moment_group_' + filenameElement.getAttribute('group').strip()
          initialisationTemplate.momentGroupName = momentGroupName
        elif kindString == 'hdf5':
          groupName = None
          if filenameElement.hasAttribute('group'):
            groupName = filenameElement.getAttribute('group').strip()
          initialisationTemplate.groupName = groupName
        
        initialisationTemplate.codeBlocks['initialisation'] = createInitialisationCodeBlock()
        
        filename = filenameElement.innerText()
        if filename.isspace():
          raise ParserException(filenameElement, "The contents of the filename tag must be non-empty.")
        
        initialisationTemplate.filename = filename
        
      else:
        raise ParserException(initialisationElement, "Initialisation kind '%(kindString)s' is unrecognised.\n"
                                                     "The options are 'code' (default), 'hdf5', 'xsil', or 'zero' "
                                                     "(this is the same as having no initialisation element)." % locals())
      
      # Untie the old initialiser from the vector
      # Probably not strictly necessary
      if not vectorTemplate.initialiser == initialisationTemplate:
        vectorTemplate.initialiser.vector = None
        vectorTemplate.initialiser.remove()
      initialisationTemplate.vector = vectorTemplate
      vectorTemplate.initialiser = initialisationTemplate
      
      self.parseFeatureAttributes(initialisationElement, initialisationTemplate)
    
    return vectorTemplate
  
  def parseComputedVectorElements(self, parentElement, parentTemplate):
    results = []
    computedVectorElements = parentElement.getChildElementsByTagName('computed_vector', optional=True)
    for computedVectorElement in computedVectorElements:
      # Add the computed vector template to the results
      results.append(self.parseComputedVectorElement(computedVectorElement, parentTemplate))
    
    return results
  
  def parseComputedVectorElement(self, computedVectorElement, parentTemplate):
    if not computedVectorElement.hasAttribute('name') or len(computedVectorElement.getAttribute('name')) == 0:
      raise ParserException(computedVectorElement, "Each computed vector element must have a non-empty 'name' attribute")
    
    vectorName = computedVectorElement.getAttribute('name')
    
    # Check that this vector name is unique
    for field in self.globalNameSpace['fields']:
      if len(filter(lambda x: x.name == vectorName, field.vectors)) > 0:
        raise ParserException(computedVectorElement, "Computed vector name '%(vectorName)s' conflicts with a "
                                                     "previously defined vector of the same name" % locals())
    
    ## Check that the name isn't already taken
    if vectorName in self.globalNameSpace['symbolNames']:
      raise ParserException(computedVectorElement, "Computed vector name '%(vectorName)s' conflicts with previously "
                                                   "defined symbol of the same name." % locals())
    
    ## Make sure no-one else takes the name
    self.globalNameSpace['symbolNames'].add(vectorName)
    
    if not computedVectorElement.hasAttribute('dimensions'):
      dimensionNames = self.globalNameSpace['geometry'].primaryTransverseDimensionNames
    elif len(computedVectorElement.getAttribute('dimensions').strip()) == 0:
      # No dimensions
      dimensionNames = []
    else:
      dimensionsString = computedVectorElement.getAttribute('dimensions').strip()
      dimensionNames = Utilities.symbolsInString(dimensionsString, xmlElement = computedVectorElement)
      if not dimensionNames:
        raise ParserException(computedVectorElement, "Cannot understand '%(dimensionsString)s' as a "
                                                     "list of dimensions" % locals())
        
    
    fieldTemplate = FieldElementTemplate.sortedFieldWithDimensionNames(dimensionNames, xmlElement = computedVectorElement)
    
    typeString = None
    if computedVectorElement.hasAttribute('type'):
      typeString = computedVectorElement.getAttribute('type').lower()
    
    if typeString in (None, 'complex'):
      typeString = 'complex'
    elif typeString == 'real':
      typeString = 'real'
    else:
      raise ParserException(
        computedVectorElement,
        "Unknown type '%(typeString)s'. "
        "Options are 'complex' (default), or 'real'" % locals()
      )
    
    if parentTemplate is None:
      parentTemplate = fieldTemplate
    # One way or another, we now have our fieldTemplate
    # So we can now construct the computed vector template
    vectorTemplate = ComputedVectorTemplate(name = vectorName, field = fieldTemplate,
                                            parent = parentTemplate, type = typeString,
                                            xmlElement = computedVectorElement,
                                            **self.argumentsToTemplateConstructors)
    
    self.globalNameSpace['simulationVectors'].append(vectorTemplate)
    
    componentsElement = computedVectorElement.getChildElementByTagName('components')
    
    
    componentsString = componentsElement.innerText()
    if not componentsString:
      raise ParserException(componentsElement, "The components element must not be empty")
    
    results = Utilities.symbolsInString(componentsString, componentsElement)
    
    if not results:
      raise ParserException(componentsElement, "Could not extract component names from component string "
                                               "'%(componentsString)s'." % locals())
    
    for componentName in results:
      if componentName in self.globalNameSpace['symbolNames']:
        raise ParserException(componentsElement, "Component name '%(componentName)s' conflicts with "
                                                 "a previously-defined symbol of the same name." % locals())
      self.globalNameSpace['symbolNames'].add(componentName)
      
      vectorTemplate.components.append(componentName)
    
    evaluationElement = computedVectorElement.getChildElementByTagName('evaluation')
    evaluationCodeBlock = _UserLoopCodeBlock(field = None, xmlElement = evaluationElement,
                                             parent = vectorTemplate, **self.argumentsToTemplateConstructors)
    evaluationCodeBlock.dependenciesEntity = self.parseDependencies(evaluationElement, optional=True)
    evaluationCodeBlock.targetVector = vectorTemplate
    vectorTemplate.codeBlocks['evaluation'] = evaluationCodeBlock
    
    self.parseFeatureAttributes(evaluationElement, vectorTemplate)
    
    return vectorTemplate
  
  
  def parseNoiseVectorElements(self, parentElement, parentTemplate):
    results = []
    noiseVectorElements = parentElement.getChildElementsByTagName('noise_vector', optional=True)
    for noiseVectorElement in noiseVectorElements:
      # Add the noise vector template to the results
      results.append(self.parseNoiseVectorElement(noiseVectorElement, parentTemplate))
    
    if noiseVectorElements and not 'Stochastic' in self.globalNameSpace['features']:
      Features.Stochastic.Stochastic(parent = self.simulation, **self.argumentsToTemplateConstructors)
    
    
    return results
  
  def parseNoiseVectorElement(self, noiseVectorElement, parentTemplate):
    if not noiseVectorElement.hasAttribute('name') or len(noiseVectorElement.getAttribute('name')) == 0:
      raise ParserException(noiseVectorElement, "Each noise vector element must have a non-empty 'name' attribute")
    
    vectorName = noiseVectorElement.getAttribute('name')
    
    # Check that this vector name is unique
    for field in self.globalNameSpace['fields']:
      if len(filter(lambda x: x.name == vectorName, field.vectors)) > 0:
        raise ParserException(noiseVectorElement, "Noise vector name '%(vectorName)s' conflicts with a "
                                                     "previously defined vector of the same name" % locals())
    
    ## Check that the name isn't already taken
    if vectorName in self.globalNameSpace['symbolNames']:
      raise ParserException(noiseVectorElement, "Noise vector name '%(vectorName)s' conflicts with previously "
                                                   "defined symbol of the same name." % locals())
    
    ## Make sure no-one else takes the name
    self.globalNameSpace['symbolNames'].add(vectorName)
    
    if not noiseVectorElement.hasAttribute('dimensions'):
      dimensionNames = self.globalNameSpace['geometry'].primaryTransverseDimensionNames
    elif len(noiseVectorElement.getAttribute('dimensions').strip()) == 0:
      # No dimensions
      dimensionNames = []
    else:
      dimensionsString = noiseVectorElement.getAttribute('dimensions').strip()
      dimensionNames = Utilities.symbolsInString(dimensionsString, xmlElement = noiseVectorElement)
      if not dimensionNames:
        raise ParserException(noiseVectorElement, "Cannot understand '%(dimensionsString)s' as a "
                                                     "list of dimensions" % locals())
    
    
    fieldTemplate = FieldElementTemplate.sortedFieldWithDimensionNames(dimensionNames, xmlElement = noiseVectorElement)

    # Backwards compatibility
    if noiseVectorElement.hasAttribute('initial_space'):
      basis_string = noiseVectorElement.getAttribute('initial_space')
      noiseVectorElement.setAttribute('initial_basis', basis_string)
    
    if noiseVectorElement.hasAttribute('initial_basis'):
      initialBasis = fieldTemplate.basisFromString(
          noiseVectorElement.getAttribute('initial_basis'),
          xmlElement = noiseVectorElement
      )
    else:
      initialBasis = fieldTemplate.defaultCoordinateBasis
    
    typeString = None
    if noiseVectorElement.hasAttribute('type'):
      typeString = noiseVectorElement.getAttribute('type').lower()
    
    if not noiseVectorElement.hasAttribute('kind') or len(noiseVectorElement.getAttribute('kind')) == 0:
      raise ParserException(noiseVectorElement, "Each noise vector element must have a non-empty 'kind' attribute")
    
    vectorKind = noiseVectorElement.getAttribute('kind').strip().lower()
    vectorMethod = None
    if noiseVectorElement.hasAttribute('method'):
      vectorMethod = noiseVectorElement.getAttribute('method').lower()
    else:
      vectorMethod = 'posix'
    
    randomVariableClass = None
    generatorClass = None
    static = None
    randomVariableAttributeDictionary = dict()
    
    if vectorKind in ('gauss', 'gaussian', 'wiener'):
      static = True
      if vectorKind == 'wiener':
        static = False
      randomVariableClass, generatorClass = {
        'mkl': (GaussianMKLRandomVariable, MKLGenerator),
        'dsfmt': (GaussianBoxMuellerRandomVariable, DSFMTGenerator),
        'posix': (GaussianBoxMuellerRandomVariable, POSIXGenerator),
        'solirte': (GaussianSolirteRandomVariable, SolirteGenerator),
      }.get(vectorMethod,(None,None))
      if not generatorClass:
        raise ParserException(noiseVectorElement, "Method '%(vectorMethod)s' for Gaussian noises is unknown.  Legal possibilities include 'mkl', 'dsfmt', 'posix' and 'solirte'." % locals())
    
    elif vectorKind == 'uniform':
      static = True
      randomVariableClass = UniformRandomVariable
      generatorClass = {
        'mkl': MKLGenerator,
        'dsfmt': DSFMTGenerator,
        'posix': POSIXGenerator,
        'solirte': SolirteGenerator,
      }.get(vectorMethod)
      if not generatorClass:
        raise ParserException(noiseVectorElement, "Method '%(vectorMethod)s' for uniform noises is unknown." % locals())
    
    elif vectorKind in ('poissonian','jump'):
      if typeString == 'complex':
        raise ParserException(noiseVectorElement, "Poissonian noises cannot be complex-valued.")        
      randomVariableClass = PoissonianRandomVariable
      if vectorKind == 'jump':
        static = False
        if noiseVectorElement.hasAttribute('mean-rate'):
          meanRateString = noiseVectorElement.getAttribute('mean-rate')
          meanRateAttributeName = 'mean-rate'
        else:  
          raise ParserException(noiseVectorElement, "Jump noises must specify a 'mean-rate' attribute.")
      elif vectorKind == 'poissonian':
        static = True
        if noiseVectorElement.hasAttribute('mean-density'):
          meanRateString = noiseVectorElement.getAttribute('mean-density')
          meanRateAttributeName = 'mean-density'
        elif noiseVectorElement.hasAttribute('mean'):
          meanRateString = noiseVectorElement.getAttribute('mean')
          meanRateAttributeName = 'mean'
        else:  
          raise ParserException(noiseVectorElement, "Poissonian noise must specify a 'mean-density' or 'mean' attribute.")
          
      if vectorMethod == 'posix': 
        generatorClass = POSIXGenerator
      elif vectorMethod == 'dsfmt':
          generatorClass = DSFMTGenerator
      else:
        raise ParserException(noiseVectorElement, "Method '%(vectorMethod)s' for Poissonian and Jump noises is unknown." % locals())
      
      try:
        meanRate = float(meanRateString) # Is it a simple number?
        if meanRate < 0.0:               # Was the number positive?
          raise ParserException(noiseVectorElement, "The %(meanRateAttributeName)s for Poissonian noises must be positive." % locals())
      except ValueError, err:
        # We could just barf now, but it could be valid code, and there's no way we can know.
        # But we only accept code for this value when we have a validation element with a 
        # run-time kind of validation check
        if 'Validation' in self.globalNameSpace['features']:
          validationFeature = self.globalNameSpace['features']['Validation']
          validationFeature.validationChecks.append("""
          if (%(meanRateString)s < 0.0)
            _LOG(_ERROR_LOG_LEVEL, "ERROR: The %(meanRateAttributeName)s for Poissonian noise %(vectorName)s is not positive!\\n"
                                   "Mean-rate = %%e\\n", %(meanRateString)s);""" % locals())
        else:
          raise ParserException(
            noiseVectorElement,
            "Unable to understand '%(meanRateString)s' as a positive real value. "
            "Use the feature <validation kind=\"run-time\"/> to allow for arbitrary code." % locals()
          )
      randomVariableAttributeDictionary['noiseMeanRate'] = meanRateString
    else:
      raise ParserException(noiseVectorElement, "Unknown noise kind '%(kind)s'." % locals())
    
    if static is None:
      raise ParserException(
          noiseVectorElement, 
          "Internal error: Noise type is not defined as static or dynamic. "
          "Please report this error to %s." % self.globalNameSpace['bugReportAddress'])
    
    if typeString in (None, 'complex'):
      typeString = 'complex'
    elif typeString == 'real':
      typeString = 'real'
    else:
      raise ParserException(noiseVectorElement,
        "Unknown type '%(typeString)s'. "
        "Options are 'complex' (default), or 'real'" % locals()
      )
    
    if parentTemplate is None:
      parentTemplate = fieldTemplate
    # One way or another, we now have our fieldTemplate
    # So we can now construct the noise vector template
    vectorTemplate = NoiseVectorTemplate(
      name = vectorName, field = fieldTemplate, staticNoise = static,
      parent = parentTemplate, initialBasis = initialBasis,
      type = typeString, xmlElement = noiseVectorElement,
      **self.argumentsToTemplateConstructors
    )
    
    self.globalNameSpace['simulationVectors'].append(vectorTemplate)
    
    
    componentsElement = noiseVectorElement.getChildElementByTagName('components')
    
    componentsString = componentsElement.innerText()
    if not componentsString:
      raise ParserException(componentsElement, "The components element must not be empty")
    
    results = Utilities.symbolsInString(componentsString, componentsElement)
    
    if not results:
      raise ParserException(componentsElement, "Could not extract component names from component string "
                                               "'%(componentsString)s'." % locals())
    
    for componentName in results:
      if componentName in self.globalNameSpace['symbolNames']:
        raise ParserException(componentsElement, "Component name '%(componentName)s' conflicts with "
                                                 "a previously-defined symbol of the same name." % locals())
      self.globalNameSpace['symbolNames'].add(componentName)
    
      vectorTemplate.components.append(componentName)
      
    randomVariable = randomVariableClass(parent = vectorTemplate, **self.argumentsToTemplateConstructors)
    vectorTemplate._children.append(randomVariable)
    generator = generatorClass(parent = randomVariable, **self.argumentsToTemplateConstructors)
    randomVariable._children.append(generator)
    
    self.applyAttributeDictionaryToObject(randomVariableAttributeDictionary, randomVariable)
    
    generator.seedArray = []
    if noiseVectorElement.hasAttribute('seed'):
      seedStringList = noiseVectorElement.getAttribute('seed').split()
      for seedString in seedStringList:
        try:
          seedInt = int(seedString)
          if seedInt < 0:
            raise ParserException(noiseVectorElement, "Seeds must be positive integers." % locals())
        except ValueError, err:
          if 'Validation' in self.globalNameSpace['features']:
            validationFeature = self.globalNameSpace['features']['Validation']
            validationFeature.validationChecks.append("""
            if (%(seedString)s < 0)
              _LOG(_ERROR_LOG_LEVEL, "ERROR: The seed for this noise vector is not positive!\\n"
              "Seed = %%d\\n", %(seedString)s);""" % locals())
          else:
            raise ParserException(noiseVectorElement, "Unable to understand seed '%(seedString)s' as a positive integer. Use the feature <validation kind=\"run-time\"/> to allow for arbitrary code." % locals())
      generator.seedArray = seedStringList
      
    generator.generatorName = '_gen_'+vectorName
    randomVariable.generator = generator
      
    vectorTemplate.randomVariable = randomVariable

    return vectorTemplate


  def parseTopLevelSequenceElement(self, simulationElement):
    topLevelSequenceElement = simulationElement.getChildElementByTagName('sequence')
    
    topLevelSequenceElementTemplate = TopLevelSequenceElementTemplate(**self.argumentsToTemplateConstructors)
    
    self.parseSequenceElement(topLevelSequenceElement, topLevelSequenceElementTemplate)
  
  def parseSequenceElement(self, sequenceElement, sequenceTemplate):
    if sequenceElement.hasAttribute('cycles'):
      cyclesString = sequenceElement.getAttribute('cycles')
      try:
        cycles = int(cyclesString)
      except ValueError, err:
        raise ParserException(sequenceElement, "Unable to understand '%(cyclesString)s' as an integer.")
      
      if cycles <= 0:
        raise ParserException(sequenceElement, "The number of cycles must be positive.")
      
      sequenceTemplate.localCycles = cycles
    
    for childNode in sequenceElement.childNodes:
      if not childNode.nodeType == minidom.Node.ELEMENT_NODE:
        continue
      
      tagName = childNode.tagName.lower()
      
      if tagName == 'integrate':
        integrateTemplate = self.parseIntegrateElement(childNode)
        sequenceTemplate.addSegment(integrateTemplate)
      elif tagName == 'filter':
        # Construct the filter segment
        filterSegmentTemplate = FilterSegmentTemplate(xmlElement = childNode,
                                                      **self.argumentsToTemplateConstructors)
        # Add it to the sequence element as a child segment
        sequenceTemplate.addSegment(filterSegmentTemplate)
        # Create an operator container to house the filter operator
        operatorContainer = OperatorContainerTemplate(parent = filterSegmentTemplate,
                                                      **self.argumentsToTemplateConstructors)
        # Add the operator container to the filter segment
        filterSegmentTemplate.operatorContainers.append(operatorContainer)
        # parse the filter operator
        filterOperator = self.parseFilterOperator(childNode, operatorContainer)
      elif tagName == 'breakpoint':
        # Construct the breakpoint segment
        breakpointSegmentTemplate = BreakpointSegmentTemplate(xmlElement = childNode,
                                                              **self.argumentsToTemplateConstructors)
        # Add it to the sequence element as a child segment
        sequenceTemplate.addSegment(breakpointSegmentTemplate)
        # parse a dependencies element
        breakpointSegmentTemplate.dependenciesEntity = self.parseDependencies(childNode)
        
        if childNode.hasAttribute('filename'):
          breakpointSegmentTemplate.filename = childNode.getAttribute('filename').strip()
        else:
          parserWarning(childNode, "Breakpoint names defaulting to the sequence 1.xsil, 2.xsil, etc.")
        
        if childNode.hasAttribute('format'):
          formatString = childNode.getAttribute('format').strip().lower()
          outputFormatClass = Features.OutputFormat.OutputFormat.outputFormatClasses.get(formatString)
          if not outputFormatClass:
            validFormats = ', '.join(["'%s'" % formatName for formatName in Features.OutputFormat.OutputFormat.outputFormatClasses.keys()])
            raise ParserException(childNode, "Breakpoint format attribute '%(formatString)s' unknown.\n"
                                             "The valid formats are %(validFormats)s." % locals())
          outputFormat = outputFormatClass(parent = breakpointSegmentTemplate, **self.argumentsToTemplateConstructors)
          
          breakpointSegmentTemplate.outputFormat = outputFormat
      
      elif tagName == 'sequence':
        # Construct the sequence segment
        sequenceSegmentTemplate = SequenceSegmentTemplate(**self.argumentsToTemplateConstructors)
        sequenceTemplate.addSegment(sequenceSegmentTemplate)
        
        self.parseSequenceElement(childNode, sequenceSegmentTemplate)
      else:
        raise ParserException(childNode, "Unknown child of sequence element. "
                                         "Possible children include 'sequence', 'integrate', 'filter' or 'breakpoint' elements.")
    
  
  def parseIntegrateElement(self, integrateElement):
    if not integrateElement.hasAttribute('algorithm'):
      raise ParserException(integrateElement, "Integration element must have an 'algorithm' attribute.")
    
    integratorTemplateClass = None
    stepperTemplateClass = None
    algorithmSpecificOptionsDict = dict()
    
    algorithmString = integrateElement.getAttribute('algorithm')
    algorithmMap = {
      'SI':    (Integrators.FixedStep.FixedStep,                   Integrators.SIStepper.SIStepper),
      'RK4':   (Integrators.FixedStep.FixedStep,                   Integrators.RK4Stepper.RK4Stepper),
      'RK9':   (Integrators.FixedStep.FixedStep,                   Integrators.RK9Stepper.RK9Stepper),
      'RK45':  (Integrators.FixedStep.FixedStep,                   Integrators.RK45Stepper.RK45Stepper),
      'RK89':  (Integrators.FixedStep.FixedStep,                   Integrators.RK89Stepper.RK89Stepper),
      'ARK45': (Integrators.AdaptiveStep.AdaptiveStep,             Integrators.RK45Stepper.RK45Stepper),
      'ARK89': (Integrators.AdaptiveStep.AdaptiveStep,             Integrators.RK89Stepper.RK89Stepper),
      'SIC':   (Integrators.FixedStepWithCross.FixedStepWithCross, Integrators.SICStepper.SICStepper),
      'MM':    (Integrators.FixedStep.FixedStep, Integrators.MMStepper.MMStepper),
      'REMM':  (Integrators.RichardsonFixedStep.RichardsonFixedStep, Integrators.MMStepper.MMStepper),
      'BS':    (Integrators.RichardsonFixedStep.RichardsonFixedStep, Integrators.MMStepper.MMStepper), # Synonym for REMM
      'RERK4': (Integrators.RichardsonFixedStep.RichardsonFixedStep, Integrators.RK4Stepper.RK4Stepper),
      'RERK9': (Integrators.RichardsonFixedStep.RichardsonFixedStep, Integrators.RK9Stepper.RK9Stepper),
      'RESI':  (Integrators.RichardsonFixedStep.RichardsonFixedStep, Integrators.SIStepper.SIStepper),
    }
    integratorTemplateClass, stepperTemplateClass = algorithmMap.get(algorithmString, (None, None))
    
    if not integratorTemplateClass:
      raise ParserException(
        integrateElement,
        "Unknown algorithm '%s'. "
        "Options are %s." % (algorithmString, ', '.join(algorithmMap.keys())))
    
    if algorithmString == 'RK45':
      parserWarning(
        integrateElement,
        "RK45 is probably not the algorithm you want. RK45 is a 5th-order algorithm with embedded 4th-order "
        "where the 4th-order results are just thrown away. Unless you know what you are doing, you probably meant RK4 or ARK45."
      )
    elif algorithmString == 'RK89':
      parserWarning(
        integrateElement,
        "RK89 is probably not the algorithm you want. RK89 is a 9th-order algorithm with embedded 8th-order "
        "where the 8th-order results are just thrown away. Unless you know what you are doing, you probably meant RK9 or ARK89."
      )
    elif algorithmString == 'MM':
      parserWarning(
        integrateElement,
        "You have selected the Modified Midpoint Stepper directly. To use the full functionality of this "
        "stepper, use 'REMM' instead, which is Richardson Extrapolation using the Modified Midpoint Stepper."
      )  
    elif algorithmString in ['SI','SIC']:
      if integrateElement.hasAttribute('iterations'):
        algorithmSpecificOptionsDict['iterations'] = RegularExpressionStrings.integerInString(integrateElement.getAttribute('iterations'))
        if algorithmSpecificOptionsDict['iterations'] < 1:
          raise ParserException(integrateElement, "Iterations element must be 1 or greater (default 3).")
    
    integratorTemplate = integratorTemplateClass(stepperClass = stepperTemplateClass, **self.argumentsToTemplateConstructors)
    self.applyAttributeDictionaryToObject(algorithmSpecificOptionsDict, stepperTemplateClass)
    
    if integrateElement.hasAttribute('home_space'):
      attributeValue = integrateElement.getAttribute('home_space').strip().lower()
      if attributeValue == 'k':
        integratorTemplate.homeBasis = self.globalNameSpace['geometry'].defaultSpectralBasis
      elif attributeValue == 'x':
        integratorTemplate.homeBasis = self.globalNameSpace['geometry'].defaultCoordinateBasis
      else:
        raise ParserException(integrateElement, "home_space must be either 'k' or 'x'.")
    else:
      integratorTemplate.homeBasis = self.globalNameSpace['geometry'].defaultCoordinateBasis
    
    if issubclass(integratorTemplateClass, Integrators.AdaptiveStep.AdaptiveStep):
      if not integrateElement.hasAttribute('tolerance'):
        raise ParserException(integrateElement, "Adaptive integrators need a 'tolerance' attribute.")
      else:
        toleranceString = integrateElement.getAttribute('tolerance').strip()
        try:
          tolerance = float(toleranceString)
          if tolerance <= 0.0:
            raise ParserException(integrateElement, "Tolerance must be positive.")
          minTolerance = {'single': 2**-21, 'double': 2**-50}[self.globalNameSpace['precision']]
          if 'ErrorCheck' in self.globalNameSpace['features']:
            minTolerance *= 16
          if tolerance < minTolerance:
            raise ParserException(
              integrateElement,
              "Requested integration tolerance '%s' is smaller than the machine precision for %s precision arithmetic %.1e." % (toleranceString, self.globalNameSpace['precision'], minTolerance)
            )
        except ValueError, err:
          raise ParserException(integrateElement, "Could not understand tolerance '%(toleranceString)s' "
                                                  "as a number." % locals())
        
        integratorTemplate.tolerance = tolerance
      
      # FIXME: The adaptive integrators need both an absolute and a relative cutoff
      if not integrateElement.hasAttribute('cutoff'):
        pass
      else:
        cutoffString = integrateElement.getAttribute('cutoff').strip()
        try:
          cutoff = float(cutoffString)
          if not 0.0 < cutoff <= 1.0:
            raise ParserException(integrateElement, "Cutoff must be in the range (0.0, 1.0].")
        except ValueError, err:
          raise ParserException(integrateElement, "Could not understand cutoff '%(cutoffString)s' "
                                                  "as a number." % locals())
        integratorTemplate.cutoff = cutoff
        
    if integrateElement.hasAttribute('extrapolations'):
      if isinstance(integratorTemplate, Integrators.RichardsonFixedStep.RichardsonFixedStep):
        extrapolations = RegularExpressionStrings.integerInString(integrateElement.getAttribute('extrapolations'))
        if extrapolations < 1:
          raise ParserException(integrateElement, "Extrapolations element must be 1 or greater (default 4).")
        else:
          integratorTemplate.extrapolations = extrapolations
      else:
        parserWarning(
          integrateElement,
          "Extrapolations attribute is only applicable to fixed step Richardson Extrapolation integrators (including \'BS\'). "
          "This attribute will been ignored."
        )
          
    if not integrateElement.hasAttribute('interval'):
      raise ParserException(integrateElement, "Integrator needs 'interval' attribute.")
    
    intervalString = integrateElement.getAttribute('interval')
    # Now check if the interval is a valid number or variable
    try:
      interval = float(intervalString) # Is it a simple number?
      if interval <= 0.0:              # Was the number positive?
        raise ParserException(integrateElement, "Interval must be positive.")
    except ValueError, err:
      # We could just barf now, but it could be valid code, and there's no way we can know.
      # But we only accept code for this value when we have a validation element with a 
      # run-time kind of validation check
      if 'Validation' in self.globalNameSpace['features']:
        validationFeature = self.globalNameSpace['features']['Validation']
        segmentNumber = integratorTemplate.segmentNumber
        validationFeature.validationChecks.append("""
        if (%(intervalString)s <= 0.0)
          _LOG(_ERROR_LOG_LEVEL, "ERROR: The interval for segment %(segmentNumber)i is not positive!\\n"
                                 "Interval = %%e\\n", %(intervalString)s);""" % locals())
      else:
        raise ParserException(integrateElement, "Could not understand interval '%(intervalString)s' "
                                                "as a number. Use the feature <validation kind=\"run-time\"/> to allow for arbitrary code." % locals())
    
    integratorTemplate.interval = intervalString
    
    if not integrateElement.hasAttribute('steps') and isinstance(integratorTemplate, Integrators.FixedStep.FixedStep):
      raise ParserException(integrateElement, "Fixed-step integrators require a 'steps' attribute.")
    
    if integrateElement.hasAttribute('steps'):
      stepsString = integrateElement.getAttribute('steps').strip()
      if not stepsString.isdigit():
        raise ParserException(integrateElement, "Could not understand steps '%(stepsString)s' "
                                                "as a positive integer." % locals())
      
      steps = int(stepsString)
      integratorTemplate.stepCount = steps
    
    samplesElement = integrateElement.getChildElementByTagName('samples', optional=True)
    if samplesElement:
        samplesString = samplesElement.innerText()
    
        results = RegularExpressionStrings.integersInString(samplesString)
    
        if not results:
          raise ParserException(samplesElement, "Could not understand '%(samplesString)s' "
                                                "as a list of integers" % locals())
    
        if filter(lambda x: x < 0, results):
          raise ParserException(samplesElement, "All sample counts must be greater than zero.")
    
        integratorTemplate.samplesEntity = ParsedEntity(samplesElement, results)
    
    integratorTemplate.localVectors.update(self.parseComputedVectorElements(integrateElement, integratorTemplate))
    
    integratorTemplate.localVectors.update(self.parseNoiseVectorElements(integrateElement, integratorTemplate))
    
    self.parseOperatorsElements(integrateElement, integratorTemplate)
    
    self.parseFiltersElements(integrateElement, integratorTemplate)
    
    self.parseFeatureAttributes(integrateElement, integratorTemplate)
    
    return integratorTemplate
  
  def parseFiltersElements(self, integrateElement, integratorTemplate):
    filtersElements = integrateElement.getChildElementsByTagName('filters', optional=True)
    
    for filtersElement in filtersElements:
      filterOperatorContainer = self.parseFilterElements(filtersElement, parent=integratorTemplate)
      
      whereString = None
      if filtersElement.hasAttribute('where'):
        whereString = filtersElement.getAttribute('where').strip().lower()
      if whereString in (None, 'step start'):
        integratorTemplate.stepStartOperatorContainers.append(filterOperatorContainer)
      elif whereString == 'step end':
        integratorTemplate.stepEndOperatorContainers.append(filterOperatorContainer)
      else:
        raise ParserException(filtersElement, "Unknown placement of filters in the 'where' tag of '%(whereString)s'.\n"
                                              "Valid options are: 'step start' (default) or 'step end'." % locals())
    
  def parseFilterElements(self, filtersElement, parent, optional = False):
    filterElements = filtersElement.getChildElementsByTagName('filter', optional = optional)
    
    if filterElements:
      operatorContainer = OperatorContainerTemplate(parent = parent,
                                                    **self.argumentsToTemplateConstructors)
    else:
      operatorContainer = None
    
    for filterElement in filterElements:
      filterTemplate = self.parseFilterOperator(filterElement, operatorContainer)
    
    return operatorContainer
  
  def parseFilterOperator(self, filterElement, parentTemplate):
    filterName = filterElement.getAttribute('name')
    
    if filterName:
        ## Check that the name isn't already taken
        if filterName in self.globalNameSpace['symbolNames']:
          raise ParserException(filterElement, "Filter name '%(filterName)s' conflicts with previously "
                                                       "defined symbol of the same name." % locals())
    
        ## Make sure no-one else takes the name
        self.globalNameSpace['symbolNames'].add(filterName)
    
    filterTemplate = FilterOperatorTemplate(parent = parentTemplate,
                                            xmlElement = filterElement, name = filterName,
                                            **self.argumentsToTemplateConstructors)
    
    codeBlock = _UserLoopCodeBlock(field = None, xmlElement = filterElement,
                                   parent = filterTemplate, **self.argumentsToTemplateConstructors)
    codeBlock.dependenciesEntity = self.parseDependencies(filterElement, optional=True)
    filterTemplate.codeBlocks['operatorDefinition'] = codeBlock
    
    return filterTemplate
  
  def parseOperatorsElements(self, integrateElement, integratorTemplate):
    operatorsElements = integrateElement.getChildElementsByTagName('operators')
    
    fieldsUsed = []
    
    for operatorsElement in operatorsElements:
      if not operatorsElement.hasAttribute('dimensions'):
        integrationVectorsElement = operatorsElement.getChildElementByTagName('integration_vectors')
        integrationVectorNames = Utilities.symbolsInString(integrationVectorsElement.innerText(), xmlElement = integrationVectorsElement)
        vectorNameMap = dict((v.name, v) for v in self.globalNameSpace['simulationVectors'])
        fields = set()
        for vectorName in integrationVectorNames:
          if not vectorName in vectorNameMap:
            raise ParserException(integrationVectorsElement, "Unknown vector '%s'." % vectorName)
          vector = vectorNameMap[vectorName]
          fields.add(vector.field)
        if not len(fields) == 1:
          raise ParserException(integrationVectorsElement, "All integration vectors must be in the same field!  Integration vectors having different dimensions must be put in separate <operators> blocks with separate <![CDATA[...]]> blocks (within the same integrator).")
        fieldTemplate = list(fields)[0]
      else:
        dimensionNames = Utilities.symbolsInString(operatorsElement.getAttribute('dimensions'), xmlElement = operatorsElement)
        
        fieldTemplate = FieldElementTemplate.sortedFieldWithDimensionNames(dimensionNames, xmlElement = operatorsElement, createIfNeeded = False)
      
      if not fieldTemplate:
        raise ParserException(operatorsElement, "There are no vectors with this combination of dimensions.")
      
      if fieldTemplate in fieldsUsed:
        parserWarning(
          operatorsElement,
          "There is more than one operators elements with this combination of dimensions. "
          "The appropriate checks aren't yet in place to make sure that you aren't shooting yourself in the foot. "
          "Are you sure you meant this?"
        )
      
      fieldsUsed.append(fieldTemplate)
      
      self.parseOperatorsElement(operatorsElement, integratorTemplate, fieldTemplate, count = fieldsUsed.count(fieldTemplate))
    
  
  def parseOperatorsElement(self, operatorsElement, integratorTemplate, fieldTemplate, count = 1):
    if count == 1:
      operatorSuffix = ''
    else:
      operatorSuffix = str(count)
    operatorContainer = OperatorContainerTemplate(field = fieldTemplate, xmlElement = operatorsElement,
                                                  name = fieldTemplate.name + operatorSuffix + '_operators',
                                                  parent = integratorTemplate,
                                                  **self.argumentsToTemplateConstructors)
    integratorTemplate.intraStepOperatorContainers.append(operatorContainer)
    
    self.parseOperatorElements(operatorsElement, operatorContainer, integratorTemplate)
  
  def parseOperatorElements(self, operatorsElement, operatorContainer, integratorTemplate):
    haveHitDeltaAOperator = False
    for childNode in operatorsElement.childNodes:
      if childNode.nodeType == minidom.Node.ELEMENT_NODE and childNode.tagName == 'operator':
        # We have an operator element
        operatorTemplate = self.parseOperatorElement(childNode, operatorContainer)
        
        if haveHitDeltaAOperator and not isinstance(operatorTemplate, (FunctionsOperatorTemplate)):
          raise ParserException(childNode, "You cannot have this kind of operator after the CDATA section\n"
                                           "of the <operators> element. The only operators that can be put\n"
                                           "after the CDATA section are 'functions' operators.")
      
      elif childNode.nodeType == minidom.Node.CDATA_SECTION_NODE:
        deltaAOperatorTemplate = self.parseDeltaAOperator(operatorsElement, operatorContainer)
        haveHitDeltaAOperator = True
    
  
  def parseDeltaAOperator(self, operatorsElement, operatorContainer):
    deltaAOperatorTemplate = DeltaAOperatorTemplate(parent = operatorContainer, xmlElement = operatorsElement,
                                                    **self.argumentsToTemplateConstructors)
    
    integrationVectorsElement = operatorsElement.getChildElementByTagName('integration_vectors')
    if integrationVectorsElement.hasAttribute('basis'):
      basis = operatorContainer.field.basisFromString(integrationVectorsElement.getAttribute('basis'))
    else:
      basis = operatorContainer.field.defaultCoordinateBasis
    
    operatorDefinitionCodeBlock = _UserLoopCodeBlock(
      field = operatorContainer.field, parent = operatorContainer, basis = basis,
      xmlElement = operatorsElement, **self.argumentsToTemplateConstructors)
    operatorDefinitionCodeBlock.dependenciesEntity = self.parseDependencies(operatorsElement, optional=True)
    
    deltaAOperatorTemplate.codeBlocks['operatorDefinition'] = operatorDefinitionCodeBlock
    
    self.parseFeatureAttributes(operatorsElement, deltaAOperatorTemplate)
    
    integrationVectorsNames = Utilities.symbolsInString(integrationVectorsElement.innerText(), xmlElement = integrationVectorsElement)
    
    if not integrationVectorsNames:
      raise ParserException(integrationVectorsElement, "Element must be non-empty.")
    
    deltaAOperatorTemplate.integrationVectorsEntity = ParsedEntity(integrationVectorsElement, integrationVectorsNames)
  
  def parseOperatorElement(self, operatorElement, operatorContainer):
    if not operatorElement.hasAttribute('kind'):
      raise ParserException(operatorElement, "Missing 'kind' attribute.")
    
    kindString = operatorElement.getAttribute('kind').strip().lower()
    
    constantString = None
    if operatorElement.hasAttribute('constant'):
      constantString = operatorElement.getAttribute('constant').strip().lower()
    
    parserMethod = None
    operatorTemplateClass = None
    
    if kindString == 'ip':
      integratorTemplate = operatorContainer.parent
      
      if integratorTemplate.supportsConstantIPOperators and not constantString:
        # Assume that the IP operator is constant
        operatorTemplateClass = ConstantIPOperatorTemplate
      elif not integratorTemplate.supportsConstantIPOperators:
        operatorTemplateClass = NonConstantIPOperatorTemplate
      elif constantString == 'yes':
        operatorTemplateClass = ConstantIPOperatorTemplate
      elif constantString == 'no':
        # We are fixed-step, but non-constant.  Warn the user as this will either be non-optimal, or lower-order than
        # what they expect
        parserWarning(operatorElement, "Using 'constant=no' with an IP operator in a fixed-step integrator is not recommended.  "
                                       "If your IP operator depends on the propagation dimension, use 'constant=yes' as this is faster.  "
                                       "If your IP operator does depend on the propagation dimension, be aware that this will almost certainly reduce the order "
                                       "of the integrator, and this is also true if you use an adaptive-step integrator.")
        
        operatorTemplateClass = NonConstantIPOperatorTemplate
      else:
        raise ParserException(operatorElement, "The 'constant' attribute must be either 'yes' or 'no'.")
      
      parserMethod = self.parseIPOperatorElement
    elif kindString == 'ex':
      if not constantString:
        # default to constant="no" because it uses less memory, and so is typically slightly faster.
        constantString = "no"
      
      parserMethod = self.parseEXOperatorElement
      if constantString == 'yes':
        operatorTemplateClass = ConstantEXOperatorTemplate
      elif constantString == 'no':
        operatorTemplateClass = NonConstantEXOperatorTemplate
      else:
        raise ParserException(operatorElement, "The constant attribute must be either 'yes' or 'no'.")
    elif kindString == 'cross_propagation':
      parserMethod = self.parseCrossPropagationOperatorElement
      operatorTemplateClass = CrossPropagationOperatorTemplate
    elif kindString == 'functions':
      parserMethod = None
      operatorTemplateClass = FunctionsOperatorTemplate
    else:
      raise ParserException(operatorElement, "Unknown operator kind '%(kindString)s'\n"
                                             "Valid options are: 'ip', 'ex', 'functions' or 'cross-propagation'." % locals())
    
    operatorTemplate = operatorTemplateClass(parent = operatorContainer,
                                             xmlElement = operatorElement,
                                             **self.argumentsToTemplateConstructors)
    
    operatorDefinitionCodeBlock = _UserLoopCodeBlock(field = operatorTemplate.field, xmlElement = operatorElement,
                                                     parent = operatorTemplate, **self.argumentsToTemplateConstructors)
    operatorDefinitionCodeBlock.dependenciesEntity = self.parseDependencies(operatorElement, optional=True)
    
    operatorTemplate.codeBlocks['operatorDefinition'] = operatorDefinitionCodeBlock
    
    if parserMethod:
      parserMethod(operatorTemplate, operatorElement)
    
    return operatorTemplate
  
  def parseIPOperatorElement(self, operatorTemplate, operatorElement):
    operatorDefinitionCodeBlock = operatorTemplate.primaryCodeBlock
    
    if operatorElement.hasAttribute('dimensions'):
      dimensionsString = operatorElement.getAttribute('dimensions').strip()
      dimensionNames = Utilities.symbolsInString(dimensionsString, xmlElement = operatorElement)
      
      for dimensionName in dimensionNames:
        if not operatorTemplate.field.hasDimensionName(dimensionName):
          raise ParserException(operatorElement, "Cannot list dimension '%(dimensionName)s' as a dimension as the integration vectors don't have this dimension." % locals())
      field = FieldElementTemplate.sortedFieldWithDimensionNames(dimensionNames, xmlElement = operatorElement)
      operatorTemplate.field = field
      operatorTemplate.primaryCodeBlock.field = field
      
    
    basis = None
    if operatorElement.hasAttribute('basis'):
      basis = operatorTemplate.field.basisFromString(operatorElement.getAttribute('basis'), xmlElement = operatorElement)
    else:
      basis = operatorTemplate.field.defaultSpectralBasis
    
    operatorDefinitionCodeBlock.basis = basis
    
    operatorNamesElement = operatorElement.getChildElementByTagName('operator_names')
    operatorNames = Utilities.symbolsInString(operatorNamesElement.innerText(), xmlElement = operatorNamesElement)
    
    if not operatorNames:
      raise ParserException(operatorNamesElement, "operator_names must not be empty.")
    
    for operatorName in operatorNames:
      if operatorName in self.globalNameSpace['symbolNames']:
        raise ParserException(operatorNamesElement,
                "Operator name '%(operatorName)s' conflicts with previously-defined symbol." % locals())
      
    operatorTemplate.operatorNames = operatorNames
    
    vectorName = operatorTemplate.id + "_field"
    
    typeString = 'complex'
    if operatorElement.hasAttribute('type'):
      typeString = operatorElement.getAttribute('type').strip().lower()
      if not typeString in ['real', 'imaginary', 'complex']:
        raise ParserException(operatorElement, "Unknown IP operator type '%(typeString)s'.\n"
                                               "The 'type' attribute must be 'real', 'imaginary' or 'complex'." % locals())
      if typeString == 'imaginary':
        typeString = 'complex'
        operatorTemplate.expFunction = 'cis'
        operatorTemplate.valueSuffix = '.Im()'
    
    operatorVectorTemplate = VectorElementTemplate(
      name = vectorName, field = operatorTemplate.field,
      parent = operatorTemplate, initialBasis = operatorTemplate.operatorBasis,
      type = typeString,
      **self.argumentsToTemplateConstructors
    )
    
    operatorVectorTemplate.needsInitialisation = False
    
    operatorDefinitionCodeBlock.targetVector = operatorVectorTemplate
    
    operatorContainer = operatorTemplate.parent
    integratorTemplate = operatorContainer.parent
    
    operatorVectorTemplate.nComponents = len(integratorTemplate.ipPropagationStepFractions) * len(operatorNames)
    operatorTemplate.operatorVector = operatorVectorTemplate
    
    return operatorTemplate
  
  def parseEXOperatorElement(self, operatorTemplate, operatorElement):
    operatorDefinitionCodeBlock = operatorTemplate.primaryCodeBlock
    
    if operatorElement.hasAttribute('basis'):
      operatorDefinitionCodeBlock.basis = \
        operatorTemplate.field.basisFromString(operatorElement.getAttribute('basis'), xmlElement = operatorElement)
    else:
      operatorDefinitionCodeBlock.basis = operatorTemplate.field.defaultSpectralBasis
    
    operatorNamesElement = operatorElement.getChildElementByTagName('operator_names')
    
    operatorNames = Utilities.symbolsInString(operatorNamesElement.innerText(), xmlElement = operatorNamesElement)
    
    if not operatorNames:
      raise ParserException(operatorNamesElement, "operator_names must not be empty.")
    
    resultVectorComponentPrefix = "_" + operatorTemplate.id
    resultVectorComponents = []
    
    for operatorName in operatorNames:
      if operatorName in self.globalNameSpace['symbolNames']:
        raise ParserException(operatorNamesElement,
                "Operator name '%(operatorName)s' conflicts with previously-defined symbol." % locals())
      # I'm not sure that we should be protecting the operator names in an EX or IP operator (except within
      # an operators element)
      
      # self.globalNameSpace['symbolNames'].add(operatorName)
    
    operatorTemplate.operatorNames = operatorNames
    
    if isinstance(operatorTemplate, ConstantEXOperatorTemplate):
      vectorName = operatorTemplate.id + "_field"
      
      operatorVectorTemplate = VectorElementTemplate(
        name = vectorName, field = operatorTemplate.field,
        parent = operatorTemplate, initialBasis = operatorTemplate.operatorBasis,
        type = 'real',
        **self.argumentsToTemplateConstructors
      )
      
      operatorVectorTemplate.needsInitialisation = False
      operatorVectorTemplate.components = operatorNames[:]
      operatorTemplate.operatorVector = operatorVectorTemplate
      
      operatorDefinitionCodeBlock.targetVector = operatorVectorTemplate
    
    vectorName = operatorTemplate.id + "_result"
    resultVector = VectorElementTemplate(
      name = vectorName, field = operatorTemplate.field,
      parent = operatorTemplate, initialBasis = operatorTemplate.field.defaultCoordinateBasis,
      type = 'real',
      **self.argumentsToTemplateConstructors
    )
    
    resultVector.needsInitialisation = False
    resultVector.components = resultVectorComponents
    operatorTemplate.resultVector = resultVector
    resultVector.basesNeeded.add(resultVector.field.basisForBasis(operatorTemplate.operatorBasis))
    
    if isinstance(operatorTemplate, NonConstantEXOperatorTemplate):
      operatorDefinitionCodeBlock.targetVector = resultVector
    
    return operatorTemplate
  
  
  def parseCrossPropagationOperatorElement(self, operatorTemplate, operatorElement):
    operatorDefinitionCodeBlock = operatorTemplate.primaryCodeBlock
    
    operatorDefinitionCodeBlock.basis = operatorDefinitionCodeBlock.field.defaultCoordinateBasis
    
    if not operatorElement.hasAttribute('algorithm'):
      raise ParserException(operatorElement, "Missing 'algorithm' attribute.")
    
    algorithmString = operatorElement.getAttribute('algorithm').strip()
    
    crossIntegratorClass = None
    crossStepperClass = None
    algorithmSpecificOptionsDict = {}
    
    integrator = operatorTemplate.parent.parent
    if algorithmString != 'SI' and isinstance(integrator, Integrators.FixedStepWithCross.FixedStepWithCross):
      raise ParserException(operatorElement, "The SIC integrator can only be used with SI cross-propagators.  Please change the algorithm of this cross-propagator to 'SI'.")      
    
    if algorithmString == 'RK4':
      crossIntegratorClass = Integrators.FixedStep.FixedStep
      crossStepperClass = Integrators.RK4Stepper.RK4Stepper
    elif algorithmString == 'SI':
      crossIntegratorClass = Integrators.FixedStep.FixedStep
      crossStepperClass = Integrators.SIStepper.SIStepper
      if operatorElement.hasAttribute('iterations'):
        algorithmSpecificOptionsDict['iterations'] = RegularExpressionStrings.integerInString(operatorElement.getAttribute('iterations'))
        if algorithmSpecificOptionsDict['iterations'] < 1:
          raise ParserException(operatorElement, "Iterations element must be 1 or greater (default 3).")
      
    else:
      raise ParserException(operatorElement, "Unknown cross-propagation algorithm '%(algorithmString)s'.\n"
                                             "The options are 'SI' or 'RK4'." % locals())
    
    crossIntegratorTemplate = crossIntegratorClass(stepperClass = crossStepperClass,
                                                   xmlElement = operatorElement,
                                                   parent = operatorTemplate,
                                                   **self.argumentsToTemplateConstructors)
    crossIntegratorTemplate.cross = True
    crossIntegratorTemplate.homeBasis = operatorDefinitionCodeBlock.basis
    
    self.applyAttributeDictionaryToObject(algorithmSpecificOptionsDict, crossIntegratorTemplate)
    
    if not operatorElement.hasAttribute('propagation_dimension'):
      raise ParserException(operatorElement, "Missing 'propagation_dimension' attribute.")
    
    propagationDimensionName = operatorElement.getAttribute('propagation_dimension').strip()
    fullField = operatorTemplate.field
    if not fullField.hasDimensionName(propagationDimensionName):
      fullFieldName = fullField.name
      raise ParserException(operatorElement, "The '%(propagationDimensionName)s' dimension must be a dimension of the\n"
                                             "'%(fullFieldName)s' field in order to cross-propagate along this dimension."
                                             % locals())
    
    operatorTemplate.propagationDimension = propagationDimensionName
    
    propagationDimension = fullField.dimensionWithName(propagationDimensionName)
    
    propDimRep = propagationDimension.representations[0]
    
    if not propDimRep.type == 'real' or not isinstance(propDimRep, UniformDimensionRepresentation):
      raise ParserException(operatorElement, "Cannot integrate in the '%(propagationDimensionName)s' direction as it is an integer-valued dimension.\n"
                                             "Cross-propagators can only integrate along normal dimensions." % locals())
    
    fieldPropagationDimensionIndex = fullField.indexOfDimension(propagationDimension)
    # Set the stepCount -- this is the lattice for this dimension minus 1 because we know the value at the starting boundary
    crossIntegratorTemplate.stepCount = ''.join(['(', propDimRep.globalLattice, ' - 1)'])
    
    boundaryConditionElement = operatorElement.getChildElementByTagName('boundary_condition')
    
    if not boundaryConditionElement.hasAttribute('kind'):
      raise ParserException(boundaryConditionElement, "The 'boundary_condition' tag must have a kind='left' or kind='right' attribute.")
    
    kindString = boundaryConditionElement.getAttribute('kind').strip().lower()
    
    if kindString == 'left':
      operatorTemplate.propagationDirection = '+'
    elif kindString == 'right':
      operatorTemplate.propagationDirection = '-'
    else:
      raise ParserException(boundaryConditionElement, "Unknown boundary condition kind '%(kindString)s'. Options are 'left' or 'right'." % locals())
    
    # Set the step
    crossIntegratorTemplate.step = operatorTemplate.propagationDirection + propDimRep.stepSize
    
    integrationVectorsElement = operatorElement.getChildElementByTagName('integration_vectors')
    integrationVectorNames = Utilities.symbolsInString(integrationVectorsElement.innerText(), xmlElement = integrationVectorsElement)
    operatorTemplate.integrationVectorsEntity = ParsedEntity(integrationVectorsElement, integrationVectorNames)
    
    # We need to construct the field element for the reduced dimensions
    reducedField = operatorTemplate.reducedDimensionFieldForField(fullField)
    operatorTemplate.reducedField = reducedField
    
    operatorContainer = OperatorContainerTemplate(field = reducedField,
                                                  parent = crossIntegratorTemplate,
                                                  **self.argumentsToTemplateConstructors)
    crossIntegratorTemplate.intraStepOperatorContainers.append(operatorContainer)
    
    boundaryConditionCodeBlock = _UserLoopCodeBlock(
      field = reducedField, xmlElement = boundaryConditionElement,
      parent = operatorTemplate, basis = operatorDefinitionCodeBlock.basis,
      **self.argumentsToTemplateConstructors)
    boundaryConditionCodeBlock.dependenciesEntity = self.parseDependencies(boundaryConditionElement, optional=True)
    
    operatorTemplate.codeBlocks['boundaryCondition'] = boundaryConditionCodeBlock
    
    
    # Now we can construct the delta a operator for the cross-propagation integrator
    # When we parse our operator elements (if we have any), the delta a operator will also be constructed
    self.parseOperatorElements(operatorElement, operatorContainer, crossIntegratorTemplate)
    
    operatorTemplate.crossPropagationIntegrator = crossIntegratorTemplate
    operatorContainer.deltaAOperator.codeBlocks['operatorDefinition'].basis = operatorDefinitionCodeBlock.basis
    operatorTemplate.crossPropagationIntegratorDeltaAOperator = operatorContainer.deltaAOperator
  
  
  def parseOutputElement(self, simulationElement):
    outputElement = simulationElement.getChildElementByTagName('output')
    
    outputFeature = Features.Output.Output(parent = self.simulation, xmlElement = outputElement,
                                           **self.argumentsToTemplateConstructors)
    
    formatName = 'hdf5'
    
    if outputElement.hasAttribute('format'):
      formatName = outputElement.getAttribute('format').strip().lower()
    
    outputFormatClass = Features.OutputFormat.OutputFormat.outputFormatClasses.get(formatName)
    if not outputFormatClass:
      validFormats = ', '.join(["'%s'" % formatType for formatType in Features.OutputFormat.OutputFormat.outputFormatClasses.keys()])
      raise ParserException(outputElement, "Breakpoint format attribute '%(formatName)s' unknown.\n"
                                           "The valid formats are %(validFormats)s." % locals())
    
    if not outputElement.hasAttribute('filename'):
      filename = self.globalNameSpace['simulationName']
    elif not outputElement.getAttribute('filename').strip():
      raise ParserException(outputElement, "Filename attribute is empty.")
    else:
      filename = outputElement.getAttribute('filename').strip()
    
    if filename.lower().endswith('.xsil'):
      index = filename.lower().rindex('.xsil')
      filename = filename[0:index]
    
    outputFormat = outputFormatClass(parent = outputFeature, xmlElement = outputElement,
                                     **self.argumentsToTemplateConstructors)
    outputFeature.filename = filename
    outputFeature._children.append(outputFormat)
    outputFeature.outputFormat = outputFormat
    
    geometryTemplate = self.globalNameSpace['geometry']
    
    geometryDimRepNameMap = {}
    for dim in geometryTemplate.transverseDimensions: # Skip the propagation dimension
        for dimRep in dim.representations:
            geometryDimRepNameMap[dimRep.name] = dim
    
    
    momentGroupElements = outputElement.getChildElementsByTagNames(['group', 'sampling_group'], optional=True)
    for momentGroupNumber, momentGroupElement in enumerate(momentGroupElements):
      samplingElement = momentGroupElement if momentGroupElement.tagName == 'sampling_group' else momentGroupElement.getChildElementByTagName('sampling')
      
      momentGroupTemplate = MomentGroupTemplate(number = momentGroupNumber, xmlElement = momentGroupElement,
                                                parent = self.simulation,
                                                **self.argumentsToTemplateConstructors)
      
      samplingFieldTemplate = FieldElementTemplate(name = momentGroupTemplate.name + "_sampling", parent = self.simulation,
                                                   **self.argumentsToTemplateConstructors)
      momentGroupTemplate.samplingField = samplingFieldTemplate
      
      outputFieldTemplate = FieldElementTemplate(name = momentGroupTemplate.name + "_output", parent = self.simulation,
                                                 **self.argumentsToTemplateConstructors)
      momentGroupTemplate.outputField = outputFieldTemplate
      
      momentGroupTemplate.computedVectors.update(self.parseComputedVectorElements(samplingElement, momentGroupTemplate))
      
      sampleCount = 0
      
      if samplingElement.hasAttribute('initial_sample'):
        if samplingElement.getAttribute('initial_sample').strip().lower() == 'yes':
          momentGroupTemplate.requiresInitialSample = True
          sampleCount = 1
      
      transformMultiplexer = self.globalNameSpace['features']['TransformMultiplexer']
      samplingDimension = Dimension(name = self.globalNameSpace['globalPropagationDimension'],
                                    transverse = False,
                                    transform = transformMultiplexer.transformWithName('none'),
                                    parent = momentGroupTemplate.outputField,
                                    **self.argumentsToTemplateConstructors)
      
      propagationDimRep = NonUniformDimensionRepresentation(name = self.globalNameSpace['globalPropagationDimension'],
                                                            type = 'real',
                                                            runtimeLattice = sampleCount,
                                                            parent = samplingDimension,
                                                            **self.argumentsToTemplateConstructors)
      samplingDimension.addRepresentation(propagationDimRep)
      
      momentGroupTemplate.outputField.dimensions = [samplingDimension]
      
      basisString = samplingElement.getAttribute('basis') if samplingElement.hasAttribute('basis') else ''
      basisStringComponents = basisString.split()
      dimensionsNeedingLatticeUpdates = {}
      sampleBasis = []
      singlePointSamplingBasis = []
      
      for component in basisStringComponents:
        # Each component of the basis string is to be of the form 'dimRepName(numberOfPoints)'
        # where dimRepName is a name of a dimension in a basis,
        #       numberOfPoints is a non-negative integer,
        # and where the '(numberOfPoints)' part is optional.  If not provided, 
        # it defaults to sampling all points in that dimension.
        
        if '(' in component:
          dimRepName, latticeString = component.split('(')
        else:
          dimRepName, latticeString = component, ''
        sampleBasis.append(dimRepName)
        latticeString = latticeString.strip(')')
        if not dimRepName in geometryDimRepNameMap:
            raise ParserException(samplingElement,
                      "'%(dimRepName)s' is not recognised as a valid basis specifier." % locals())
        geometryDimension = geometryDimRepNameMap[dimRepName]
        dimRep = [rep for rep in geometryDimension.representations if rep.name == dimRepName][0]
        lattice = dimRep.runtimeLattice # Default
        if latticeString:
          try:
            lattice = int(latticeString)
          except ValueError, err:
            raise ParserException(samplingElement,
                        "Unable to interpret '%(latticeString)s' as an integer." % locals())
        
        if not isinstance(lattice, basestring):
          if not lattice >= 0:
            raise ParserException(samplingElement,
                      "Lattice size '%(latticeString)s' must be positive." % locals())
        
        # Now we check that the number of sample points is not larger than the 
        # number of points in the geometry lattice. Also check that the number of sample
        # points divide the geometry lattice (if sampling in coord space) or is smaller
        # than the total number of points (spectral or auxillary space).
        # There is an additional complication if run-time validation has been selected, and
        # the number of lattice points is a variable to be passed in at run time, rather than
        # a number given at the script parse-time.
        # If this is the case, set up the checks (e.g. sample points must be less than
        # total lattice points etc) to be done at run-time rather than here.

        # Check to see if run-time validation has been selected
        runTimeValidationSelected = False
        if 'Validation' in self.globalNameSpace['features']:
          if self.globalNameSpace['features']['Validation'].runValidationChecks == True:
            runTimeValidationSelected = True

        geometryLattice = dimRep.runtimeLattice

        if isinstance(geometryLattice, basestring):
          if runTimeValidationSelected == False:
            # Theoretically this code won't execute, since the only way geometryLattice
            # can be a run-time variable at this point is if run-time validation is
            # on. Still, make the check in case something is screwed up.
            raise ParserException(samplingElement, 
                    "Sampling: Geometry lattice not a number, and run-time validation is off! \n"
                    "This shouldn't happen. Please report this to xmds-devel@lists.sourceforge.net.\n")
          else:
            # Run-time validation is on, so we need to set up some run-time checks
            # to make sure the geometry lattice size given at run-time is sensible for
            # sampling that has been specified.
            validationFeature = self.globalNameSpace['features']['Validation']
            validationFeature.validationChecks.append("""
              if (%(lattice)s > %(geometryLattice)s)
                _LOG(_ERROR_LOG_LEVEL, "ERROR: Can't sample more points in dimension '%(dimRepName)s' than\\n"
                                       "there are points in the full dimension.\\n"
                                       "%%i > %%i.\\n", (int)%(lattice)s, (int)%(geometryLattice)s);""" % locals())
            
            # Coordinate space: the number of sample points must divide the number of geometry points
            if issubclass(dimRep.tag, dimRep.tagForName('coordinate')):
              validationFeature.validationChecks.append("""
                if ( (%(lattice)s > 0) && (%(geometryLattice)s %% %(lattice)s !=0) )
                  _LOG(_ERROR_LOG_LEVEL, "ERROR: The number of sampling lattice points (%%i) must divide the number\\n"
                                       "of lattice points on the simulation grid (%%i).\\n", (int)%(lattice)s, (int)%(geometryLattice)s);\n""" % locals())

        else:
          # the geometry lattice is a number, not a run-time variable, so we can do the 
          # following checks now 
          if lattice > geometryLattice:
            raise ParserException(samplingElement,
                        "Can't sample more points in dimension '%(dimRepName)s' than there are points in the full dimension.\n"
                        "%(lattice)i > %(geometryLattice)i." % locals())
          if issubclass(dimRep.tag, dimRep.tagForName('coordinate')):
            # Coordinate space: the number of sample points must divide the number of geometry points
            if lattice > 0 and not (geometryLattice % lattice) == 0:
              raise ParserException(samplingElement,
                        "The number of sampling lattice points (%(lattice)i) must divide the number "
                        "of lattice points on the simulation grid (%(geometryLattice)i)." % locals())
            # For spectral / auxiliary space, the number of lattice points just needs to be smaller than
            # the total number of points, something we have already checked.
        
        # This code sets up the sampling for various dimensions. There are three
        # cases: lattice>1, lattice=1, and lattice=0, where lattice is the number
        # of points to sample on the full geometry lattice.
        # If lattice>1 and lattice<geometry lattice, we're subsampling.
        # We have to note that in the case where the geometry lattice is specified
        # at runtime (so it's a string, not a number), if no number was explicitly
        # given for the sampling lattice, then it inherits the string as a value
        # from the geometry lattice. In this case, we don't need to subsample, but
        # we should be aware that lattice can be a string.
        if isinstance(lattice, basestring) or lattice > 1:
          outputFieldDimension = geometryDimension.copy(parent = outputFieldTemplate)
          if geometryLattice != lattice:
             # Yes, we are subsampling
             dimensionsNeedingLatticeUpdates[outputFieldDimension.name] = lattice
          samplingFieldTemplate.dimensions.append(outputFieldDimension.copy(parent = samplingFieldTemplate))
          outputFieldTemplate.dimensions.append(outputFieldDimension)
        elif lattice == 1:
          # In this case, we don't want the dimension in either the moment group, or the sampling field.
          # But we do want it in the sampling basis, we have to add it at the end
          singlePointSamplingBasis.append(dimRepName)
        elif lattice == 0:
          # In this case, the dimension only belongs to the sampling field because we are integrating over it.
          # Note that we previously set the lattice of the dimension to be the same as the number
          # of points in this dimension according to the geometry element.
          samplingFieldTemplate.dimensions.append(geometryDimension.copy(parent = samplingFieldTemplate))
          
      
      samplingFieldTemplate.sortDimensions()
      outputFieldTemplate.sortDimensions()
      
      driver = self.globalNameSpace['features']['Driver']
      
      sampleBasis = samplingFieldTemplate.basisForBasis(driver.canonicalBasisForBasis(tuple(sampleBasis)))
      outputBasis = momentGroupTemplate.outputField.basisForBasis(
        (propagationDimRep.canonicalName,) + sampleBasis
      )
      momentGroupTemplate.singlePointSamplingBasis = driver.canonicalBasisForBasis(tuple(singlePointSamplingBasis))
      
      if formatName == 'hdf5':
        # HDF5 doesn't like writing out data when the order of dimensions in the file and
        # in memory aren't the same. It's slow. So we make sure that we sample in the same
        # order that we would write out to file. But only for HDF5 as this requires extra
        # MPI Transpose operations at each sample.
        sampleBasis = driver.canonicalBasisForBasis(sampleBasis, noTranspose = True)
        outputBasis = driver.canonicalBasisForBasis(outputBasis, noTranspose = True)
      
      
      for dimName, lattice in dimensionsNeedingLatticeUpdates.items():
        for field, basis in [(samplingFieldTemplate, sampleBasis), (outputFieldTemplate, outputBasis)]:
          field.dimensionWithName(dimName).setReducedLatticeInBasis(lattice, basis)
      
      # end looping over dimension elements.  
      momentGroupTemplate.outputBasis = outputBasis
      
      rawVectorTemplate = VectorElementTemplate(
        name = 'raw', field = momentGroupTemplate.outputField,
        initialBasis = momentGroupTemplate.outputBasis, type = 'real',
        **self.argumentsToTemplateConstructors
      )
      momentGroupTemplate.rawVector = rawVectorTemplate
      
      momentsElement = samplingElement.getChildElementByTagName('moments')
      momentNames = Utilities.symbolsInString(momentsElement.innerText(), xmlElement = momentsElement)
      
      if not momentNames:
        raise ParserException(momentsElement, "Moments element should be a list of moment names")
      
      for momentName in momentNames:
        if momentName in self.globalNameSpace['symbolNames']:
          raise ParserException(momentsElement, 
                  "'%(momentName)s' cannot be used as a moment name because it clashes with "
                  "a previously-defined variable." % locals())
        
        ## We don't add the momentName to the symbol list because they can be used by other moment groups safely
        rawVectorTemplate.components.append(momentName)
      
      samplingCodeBlock = _UserLoopCodeBlock(
        field = samplingFieldTemplate, xmlElement = samplingElement,
        parent = momentGroupTemplate, basis = sampleBasis,
        **self.argumentsToTemplateConstructors)
      samplingCodeBlock.dependenciesEntity = self.parseDependencies(samplingElement)
      if samplingCodeBlock.dependenciesEntity.xmlElement.hasAttribute("basis"):
          parserWarning(samplingCodeBlock.dependenciesEntity.xmlElement, "'basis' attribute is ignored on the <dependencies> tag in a sampling block. "
                        "Instead specify the basis on the <sampling_group> tag itself.")
      # The raw vector will be needed during looping
      samplingCodeBlock.targetVector = rawVectorTemplate
      momentGroupTemplate.codeBlocks['sampling'] = samplingCodeBlock
      
      if not samplingCodeBlock.codeString:
        raise ParserException(samplingElement, "The CDATA section for the sampling code must not be empty.")
      
      operatorContainer = self.parseFilterElements(samplingElement, parent=momentGroupTemplate, optional=True)
      if operatorContainer:
        momentGroupTemplate.operatorContainers.append(operatorContainer)
      
      operatorElements = samplingElement.getChildElementsByTagName('operator', optional=True)
      if operatorElements:
        operatorContainer = OperatorContainerTemplate(field = samplingFieldTemplate,
                                                      # Point the proxies for the shared code etc at
                                                      # the moment group object's sampling code, the sampling space, etc.
                                                      sharedCodeBlockKeyPath = 'parent.codeBlocks.sampling',
                                                      parent = momentGroupTemplate,
                                                      **self.argumentsToTemplateConstructors)
        
        momentGroupTemplate.operatorContainers.append(operatorContainer)
        for operatorElement in operatorElements:
          kindString = operatorElement.getAttribute('kind').strip().lower()
          if not kindString in ('functions', 'ex'):
            raise ParserException(operatorElement, "Unrecognised operator kind '%(kindString)s'. "
                                                   "The only valid operator kinds in sampling elements are 'functions' and 'ex'." % locals())
          
          if kindString == 'ex':
            # We can't handle constant=yes in this case, so we'll just replace it with the value we can support
            operatorElement.setAttribute('constant', 'no')
          operatorTemplate = self.parseOperatorElement(operatorElement, operatorContainer)
          if isinstance(operatorTemplate, ConstantEXOperatorTemplate):
            raise ParserException(operatorElement, "You cannot have a constant EX operator in moment group sampling. Try constant=\"no\".")
      
      
      
      # We have now dealt with the sampling element, and now need to deal with the processing element.
      # TODO: Implement processing element.
      processingElement = momentGroupElement.getChildElementByTagName('post_processing', optional=True)
      
      processedVectorTemplate = VectorElementTemplate(
        name = 'processed', field = outputFieldTemplate, initialBasis = momentGroupTemplate.outputBasis,
        type = 'real',
        **self.argumentsToTemplateConstructors
      )
      momentGroupTemplate.processedVector = processedVectorTemplate
      
      if not processingElement:
        momentGroupTemplate.hasPostProcessing = False
        processedVectorTemplate.components = rawVectorTemplate.components[:]
        rawVectorTemplate.type = 'real'
      else:
        momentGroupTemplate.hasPostProcessing = True
  

