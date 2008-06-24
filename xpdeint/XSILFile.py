#!/usr/bin/env python
# encoding: utf-8
"""
XSILFile.py

Created by Graham Dennis on 2008-06-18.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

import os
import sys
from xml.dom import minidom
import xpdeint.minidom_extras

import numpy

class XSILData(object):
  def __init__(self, independentVariables, dependentVariables):
    self.independentVariables = independentVariables
    self.dependentVariables = dependentVariables
  

class XSILDataASCII(XSILData):
  def __init__(self, independentVariables, dependentVariables, dataString):
    XSILData.__init__(self, independentVariables, dependentVariables)
    self.parseDataString(dataString)
  
  def parseDataString(self, dataString):
    lines = dataString.splitlines()
    del dataString
    varCount = len(self.independentVariables) + len(self.dependentVariables)
    indepSize = reduce(int.__mul__, [indVar['length'] for indVar in self.independentVariables])
    result = numpy.empty(indepSize*varCount)
    for lineNum, line in enumerate(lines):
      result[lineNum*varCount:((lineNum+1)*varCount)] = numpy.fromstring(line, numpy.float64, sep=' ')
    assert len(result) == indepSize*varCount
    
    result = result.reshape(indepSize, varCount)
    independentGeometry = []
    
    for varNum, ivar in enumerate(self.independentVariables):
      independentGeometry.append(ivar['length'])
      ivar['array'] = numpy.unique(result[:, varNum])
      assert len(ivar['array']) == ivar['length']
    for varNum, dvar in enumerate(self.dependentVariables):
      a = result[:, varNum + len(self.independentVariables)]
      dvar['array'] = a.reshape(*independentGeometry)


class XSILDataBinary(XSILData):
  def __init__(self, independentVariables, dependentVariables, uLong, precision, encoding, dataFile):
    XSILData.__init__(self, independentVariables, dependentVariables)
    self.dataFilename = os.path.split(dataFile)[1]
    self.parseDataFile(uLong, precision, encoding, dataFile)
  
  def parseDataFile(self, uLong, precision, encoding, dataFile):
    assert uLong in ['uint32', 'uint64']
    assert precision in ['single', 'double']
    assert encoding in ['BigEndian', 'LittleEndian']
    
    fd = file(dataFile, 'rb')
    
    byteorder = {'LittleEndian': '<', 'BigEndian': '>'}[encoding]
    unsignedLongTypeString = {'uint32': 'u4', 'uint64': 'u8'}[uLong]
    realTypeString = {'single': 'f4', 'double': 'f8'}[precision]
    
    ulongDType = numpy.dtype(byteorder + unsignedLongTypeString)
    floatDType = numpy.dtype(byteorder + realTypeString)
    
    independentGeometry = []
    
    for independentVariable in self.independentVariables:
      size = numpy.fromfile(fd, dtype=ulongDType, count=1)
      independentGeometry.append(size)
      assert size == independentVariable['length']
      a = numpy.fromfile(fd, dtype=floatDType, count=size)
      independentVariable['array'] = a
    
    for dependentVariable in self.dependentVariables:
      size = numpy.fromfile(fd, dtype=ulongDType, count=1)
      a = numpy.fromfile(fd, dtype=floatDType, count=size)
      dependentVariable['array'] = a.reshape(*independentGeometry)
    

class XSILObject(object):
  def __init__(self, name, dataObject, filename = None):
    self.name = name
    self.dataObject = dataObject
    if dataObject:
      self.independentVariables = dataObject.independentVariables
      self.dependentVariables = dataObject.dependentVariables
    self.filename = filename


class XSILFile(object):
  def __init__(self, filename, loadData=True):
    self.filename = filename
    self.xsilObjects = []
    
    xmlDocument = minidom.parse(filename)
    simulationElement = xmlDocument.getChildElementByTagName('simulation')
    xsilElements = simulationElement.getChildElementsByTagName('XSIL')
    for xsilElement in xsilElements:
      xsilName = xsilElement.getAttribute('Name')
      
      paramElement = xsilElement.getChildElementByTagName('Param')
      assert paramElement.hasAttribute('Name') and paramElement.getAttribute('Name') == 'n_independent'
      nIndependentVariables = int(paramElement.innerText())
      
      arrayElements = xsilElement.getChildElementsByTagName('Array')
      assert len(arrayElements) == 2
      
      variableArrayElement = arrayElements[0]
      dataArrayElement = arrayElements[1]
      
      assert variableArrayElement.hasAttribute('Name') and variableArrayElement.getAttribute('Name') == 'variables'
      dimElement = variableArrayElement.getChildElementByTagName('Dim')
      nVariables = int(dimElement.innerText())
      nDependentVariables = nVariables - nIndependentVariables
      assert nDependentVariables > 0
      streamElement = variableArrayElement.getChildElementByTagName('Stream')
      variableNames = streamElement.innerText().strip().split(' ')
      assert len(variableNames) == nVariables
      
      # We do str(name) here to convert unicode objects to str objects
      # It seems that numpy doesn't like unicode strings.
      independentVariables = [{'name': str(name)} for name in variableNames[0:nIndependentVariables]]
      dependentVariables = [{'name': str(name)} for name in variableNames[nIndependentVariables:]]
      
      assert len(dependentVariables) == nDependentVariables
      
      dimElements = dataArrayElement.getChildElementsByTagName('Dim')
      assert len(dimElements) == nIndependentVariables + 1
      
      for dimIndex, dimElement in enumerate(dimElements):
        if dimIndex < nIndependentVariables:
          independentVariables[dimIndex]['length'] = int(dimElement.innerText())
        else:
          assert int(dimElement.innerText()) == nVariables
      
      streamElement = dataArrayElement.getChildElementByTagName('Stream')
      metalinkElement = streamElement.getChildElementByTagName('Metalink')
      format = metalinkElement.getAttribute('Format').strip()
      # assert format == 'Binary', "ASCII format output currently unsupported"
      
      dataObject = None
      
      objectFilename = None
      
      if format == 'Binary':
        uLong = metalinkElement.getAttribute('UnsignedLong').strip()
        precision = metalinkElement.getAttribute('precision').strip()
        encoding = metalinkElement.getAttribute('Encoding').strip()
        objectFilename = streamElement.innerText().strip()
        dataFileName = os.path.join(os.path.split(filename)[0], objectFilename)
        if loadData:
          dataObject = XSILDataBinary(independentVariables, dependentVariables, uLong, precision, encoding, dataFileName)
      elif format == 'Text':
        if loadData:
          dataObject = XSILDataASCII(independentVariables, dependentVariables, streamElement.innerText().strip())
      
      self.xsilObjects.append(XSILObject(xsilName, dataObject, objectFilename))
    
  



