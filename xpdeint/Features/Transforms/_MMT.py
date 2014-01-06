#!/usr/bin/env python
# encoding: utf-8
"""
_MMT.py

Created by Graham Dennis on 2008-12-12.

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

from xpdeint.Features.Transforms._Transform import _Transform

from xpdeint.Geometry.DimensionRepresentation import DimensionRepresentation


class _MMT (_Transform):
  transformName = 'MMT'
  
  coordinateSpaceTag = DimensionRepresentation.registerTag('MMT coordinate space', parent = 'coordinate')
  spectralSpaceTag = DimensionRepresentation.registerTag('MMT spectral space', parent = 'spectral')
  auxiliarySpaceTag = DimensionRepresentation.registerTag('MMT auxiliary space', parent = 'auxiliary')
  
  def __init__(self, *args, **KWs):
    _Transform.__init__(self, *args, **KWs)
    self.basisMap = {}
  
  @property
  def children(self):
    children = super(_MMT, self).children
    [children.extend(basisDict['transformations'].values()) for basisDict in self.basisMap.values()]
    return children
  
  def globals(self):
    return '\n'.join([basisDict.get('globalsFunction')(dimName, basisDict) \
                          for dimName, basisDict in self.basisMap.items() if basisDict.get('globalsFunction')])
  
  def availableTransformations(self):
    results = []
    geometry = self.getVar('geometry')
    # Sort dimension names based on their ordering in the geometry.
    sortedDimNames = [(geometry.indexOfDimensionName(dimName), dimName) for dimName in self.basisMap]
    sortedDimNames.sort()
    sortedDimNames = [o[1] for o in sortedDimNames]
    # Create all transforms just for each dimension individually
    for dimName, basisDict in self.basisMap.items():
      dimReps = geometry.dimensionWithName(dimName).representations
      for transformPair, basis in basisDict['transformations'].items():
        basisReps = [[rep for rep in dimReps if rep.name == repName][0] for repName in transformPair]
        def addTransform(outOfPlace):
          results.append(dict(
            transformations = [transformPair],
            cost = basis.costEstimate(basisReps),
            outOfPlace = outOfPlace,
            transformFunction = basis.transformFunction,
            transformType = basis.matrixType,
          ))
        addTransform(True)
        if basis.supportsInPlaceOperation:
            addTransform(False)
    
    return results
  
