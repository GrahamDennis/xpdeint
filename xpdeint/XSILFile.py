#!/usr/bin/env python
# encoding: utf-8
"""
XSILFile.py

Created by Graham Dennis on 2008-06-18.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

import os
from xml.dom import minidom
import xpdeint.minidom_extras

h5py = None

numpy = None

def require_h5py():
  global h5py
  if not h5py:
    import h5py

def require_numpy():
  global numpy
  if not numpy:
    import numpy


class XSILData(object):
  def __init__(self, independentVariables, dependentVariables):
    self.independentVariables = independentVariables
    self.dependentVariables = dependentVariables
  

class XSILDataASCII(XSILData):
  format = 'ascii'
  
  def __init__(self, independentVariables, dependentVariables, dataString):
    XSILData.__init__(self, independentVariables, dependentVariables)
    if dataString: self.parseDataString(dataString)
  
  def parseDataString(self, dataString):
    require_numpy()
    
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
  """Class representing the binary data."""
  
  format = 'binary'
  
  def __init__(self, independentVariables, dependentVariables, uLong, precision, encoding, dataFile, loadData = True):
    XSILData.__init__(self, independentVariables, dependentVariables)
    self.filename = os.path.split(dataFile)[1]
    
    assert uLong in ['uint32', 'uint64']
    assert precision in ['single', 'double']
    assert encoding in ['BigEndian', 'LittleEndian']
    self.uLong = uLong
    self.precision = precision
    self.encoding = encoding
    
    if loadData: self.parseDataFile(uLong, precision, encoding, dataFile)
  
  def parseDataFile(self, uLong, precision, encoding, dataFile):
    assert uLong in ['uint32', 'uint64']
    assert precision in ['single', 'double']
    assert encoding in ['BigEndian', 'LittleEndian']
    
    require_numpy()
    
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
    
    if len(independentGeometry) == 0:
      independentGeometry.append(1)
    
    for dependentVariable in self.dependentVariables:
      size = numpy.fromfile(fd, dtype=ulongDType, count=1)
      a = numpy.fromfile(fd, dtype=floatDType, count=size)
      assert a.size == size, "Data file %s has incorrect size. Variable '%s' wasn't written completely." % (dataFile, dependentVariable['name'])
      dependentVariable['array'] = a.reshape(*independentGeometry)
    
  

class XSILDataHDF5(XSILData):
  """Class representing HDF5 data output."""
  
  format = 'hdf5'
  
  def __init__(self, independentVariables, dependentVariables, groupName, dataFile, loadData = True):
    XSILData.__init__(self, independentVariables, dependentVariables)
    self.filename = os.path.split(dataFile)[1]
    self.groupName = groupName
    
    if loadData: self.parseDataFile(groupName, dataFile)
  
  def parseDataFile(self, groupName, dataFile):
    require_h5py()
    f = h5py.File(dataFile, 'r')
    
    subgroup = f[groupName]
    
    for independentVariable in self.independentVariables:
      independentVariable['array'] = subgroup[independentVariable['name']].value
    
    for dependentVariable in self.dependentVariables:
      dependentVariable['array'] = subgroup[dependentVariable['name']].value
    
    # Now wasn't that easy.
  


class XSILObject(object):
  def __init__(self, name, data):
    self.name = name
    self.data = data
    if data:
      self.independentVariables = data.independentVariables
      self.dependentVariables = data.dependentVariables
  


class XSILFile(object):
  def __init__(self, filename, loadData=True):
    """Create an `XSILFile` object.
    `filename` is the filename of the XSIL file, and `loadData` specifies whether or not the
    data in the XSIL file should be loaded (if not, just the metadata is loaded).
    `loadData` can have one of the following values:
    
    - ``True`` or ``'all'``: load all data
    - ``False`` or ``'none'``: load no data
    - ``'ascii'``: load only data stored in ASCII format
    - ``'binary'``: load only data stored in binary format
    - ``'hdf5'``: load only data stored in HDF5 format
    """
    if not isinstance(loadData, basestring):
      # loadData is True or False
      loadData = {True: 'all', False: 'none'}[loadData]
    else:
      loadData = loadData.lower()
    assert loadData in ['all', 'ascii', 'binary', 'hdf5', 'none']
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
      
      data = None
      
      objectFilename = None
      
      if format == 'Binary':
        uLong = metalinkElement.getAttribute('UnsignedLong').strip()
        precision = metalinkElement.getAttribute('precision').strip()
        encoding = metalinkElement.getAttribute('Encoding').strip()
        objectFilename = streamElement.innerText().strip()
        filename = os.path.join(os.path.split(filename)[0], objectFilename)
        loadBinaryData = False
        if loadData in ['all', 'binary']: loadBinaryData = True
        data = XSILDataBinary(independentVariables, dependentVariables, uLong, precision, encoding, filename,
                                    loadData = loadBinaryData)
      elif format == 'Text':
        dataString = None
        if loadData in ['all', 'ascii']: dataString = streamElement.innerText().strip()
        
        data = XSILDataASCII(independentVariables, dependentVariables, dataString)
      elif format == 'HDF5':
        loadHDFData = False
        if loadData in ['all', 'hdf5']: loadHDFData = True
        objectFilename = streamElement.innerText().strip()
        filename = os.path.join(os.path.split(filename)[0], objectFilename)
        groupName = metalinkElement.getAttribute('Group').strip()
        data = XSILDataHDF5(independentVariables, dependentVariables, groupName, filename, loadData = loadHDFData)
      
      self.xsilObjects.append(XSILObject(xsilName, data))
    
  


