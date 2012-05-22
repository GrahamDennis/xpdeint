#!/usr/bin/env python
# encoding: utf-8
"""
_TransformMultiplexer.py

Created by Graham Dennis on 2008-12-23.

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

from xpdeint.Features._Feature import _Feature
from xpdeint.Utilities import combinations, GeneralisedBidirectionalSearch
from xpdeint.Function import Function
from xpdeint.Vectors.VectorElement import VectorElement
from xpdeint.ParserException import ParserException

import operator

class _TransformMultiplexer (_Feature):
  featureName = 'TransformMultiplexer'
  transformClasses = dict()
  
  def __init__(self, *args, **KWs):
    _Feature.__init__(self, *args, **KWs)
    self.transforms = set()
    self.availableTransformations = []
    self.neededTransformations = []
    self.transformations = []
  
  def transformWithName(self, name):
    if not name in self.transformClasses:
      return None
    cls = self.transformClasses[name]
    transformWithClass = [t for t in self.transforms if isinstance(t, cls)]
    assert 0 <= len(transformWithClass) <= 1
    if transformWithClass:
      return transformWithClass[0]
    else:
      return cls(parent = self.simulation, **self.argumentsToTemplateConstructors)
  
  def __getattribute__(self, name):
    """
    Call through to all methods on the child transforms. This should only be used for
    the 'insertCodeForFeatures' functions. We don't want this to happen for 'includes', etc.
    This is prevented from occuring because all of these methods are defined on `_ScriptElement`.
    """
    # As we are customising attribute access in this method, attempts to access attributes directly
    # would lead to infinite recursion (bad), so we must access variables specially
    
    # If the attribute isn't one that we are doing a special proxy for, then it perform as per usual.
    if not name in ['mainBegin', 'mainEnd']:
      return _Feature.__getattribute__(self, name)
    
    attributes = []
    # If we have the attribute, then we go first
    try:
      attributes.append(_Feature.__getattribute__(self, name))
    except AttributeError:
      pass
    
    # Then we add any child attributes
    transforms = _Feature.__getattribute__(self, 'transforms')
    attributes.extend([getattr(t, name) for t in transforms if t.hasattr(name)])
    
    # If neither ourself nor any of our children have this attribute, then we need to raise an AttributeError
    # the easiest way to do this is to just call the default implementation which will do this.
    # We want to do the same thing 
    if not attributes or not all([callable(attr) for attr in attributes]):
      return _Feature.__getattribute__(self, name)
    
    # If there's only one, we don't need to multiplex.
    if len(attributes) == 1:
      return attributes[0]
    
    # Create a multiplexing function and return it.
    def multiplexingFunction(*args, **KWs):
      results = [attr(*args, **KWs) for attr in attributes]
      if name == 'mainBegin':
        results.reverse()
      return ''.join([result for result in results if result is not None])
    
    return multiplexingFunction
  
  def preflight(self):
    super(_TransformMultiplexer, self).preflight()
    for transform in self.transforms:
      if hasattr(transform, 'availableTransformations'):
        for transformation in transform.availableTransformations():
          transformation.setdefault('owner', transform)
          self.availableTransformations.append(transformation)
    # We need to add a few transforms of our own.
    
    # Out-of-place copy
    self.oopCopy = dict(
      owner = self,
      transformations = [tuple()],
      cost = 1,
      outOfPlace = True,
      transformFunction = self.oopCopyTransformFunction,
      description = 'Out-of-place copy',
    )
    self.availableTransformations.append(self.oopCopy)
    
    # In-place multiply
    self.ipMultiply = dict(
      owner = self,
      transformations = [tuple()],
      cost = 1,
      scaling = True,
      transformFunction = self.ipMultiplyTransformFunction,
      description = 'In-place multiply',
    )
    
    # Out-of-place multiply
    self.oopMultiply = dict(
      owner = self,
      transformations = [tuple()],
      cost = 2,
      outOfPlace = True,
      scaling = True,
      transformFunction = self.oopMultiplyTransformFunction,
      description = 'Out-of-place multiply',
    )
  
  def buildTransformMap(self):
    # The mighty plan is to do the following for each vector:
    # 1. Convert all required spaces to the new-style spaces
    
    def transformedBasis(basis, transformationPair):
      """
      This function determines if `basis` can be transformed by the transform represented
      by `transformPair`. If `basis` can be transformed, then it returns the transformed basis,
      the matched part of the basis, and the components of the basis before and after the match.
      """
      if not transformationPair: return basis, (basis, tuple(), tuple())
      
      if not isinstance(basis, tuple): basis = tuple([basis])
      for sourceBasis, destBasis in [transformationPair, reversed(transformationPair)]:
        # Optimisation: If it's just a single-dimension transform, do it the fast way
        if not isinstance(sourceBasis, tuple):
          if not sourceBasis in basis: continue
          basis = list(basis)
          offset = basis.index(sourceBasis)
          basis[offset] = destBasis
          basis = tuple(basis)
          return basis, (basis[:offset], tuple([sourceBasis]), basis[offset+1:])
        
        for offset in range(0, len(basis)+1-len(sourceBasis)):
          if basis[offset:offset+len(sourceBasis)] == sourceBasis:
            basis = list(basis)
            basis[offset:offset+len(sourceBasis)] = destBasis
            basis = tuple(basis)
            return basis, (basis[:offset], sourceBasis, basis[offset+len(sourceBasis):])
      return None, (None, None, None)
    
    class BasisState(GeneralisedBidirectionalSearch.State):
      """
      This class represents a node in the transform graph. This node specifies
      both the current basis and also whether the data for the vector being
      transformed is currently 'in-place' (the data is stored in the same location
      as it was originally) or 'out-of-place' (the data is stored in a different location).
      This distinction is necessary as transforms such as matrix multiplication transforms
      necessitate an out-of-place operation, but overall, we require the data after the 
      complete transform to be back where it was to start with.
      """
      __slots__ = []
      availableTransformations = self.availableTransformations
      
      IN_PLACE = 0
      OUT_OF_PLACE = 1
      
      def next(self):
        """
        This function returns the next nodes in the transform graph that can be reached from this node.
        
        It iterates through all available transforms trying to find matches that can transform the current
        basis and determines the cost of doing so.
        """
        results = []
        
        currentBasis, currentState = self.location
        
        # Loop through all available transforms
        for transformID, transformation in enumerate(self.availableTransformations):
          # Loop through all basis-changes this 'transform' can handle
          for transformationPair in transformation['transformations']:
            # Does the transformPair match?
            resultBasis, (prefixBasis, matchedSourceBasis, postfixBasis) = transformedBasis(currentBasis, transformationPair)
            if not resultBasis: continue
            
            # The cost specified in the transform is per-point in dimensions not listed in the transformationPair
            # So we must multiply that cost by the product of the number of points in all other dimensions
            
            costMultiplier = reduce(
              operator.mul,
              [self.representationMap[repName].latticeEstimate \
                for repName in currentBasis if not repName in matchedSourceBasis],
              1
            )
            
            newCost = list(self.cost)
            
            # This transformation may change the state and/or the basis.
            # Here we consider state changes like in-place <--> out-of-place
            # and multiplying the data by a constant
            resultState = currentState
            if transformation.get('outOfPlace', False):
              resultState = {
                BasisState.IN_PLACE: BasisState.OUT_OF_PLACE,
                BasisState.OUT_OF_PLACE: BasisState.IN_PLACE
              }[currentState]
              
              # Now you might think that we're violating the cost >= 0 requirement here
              # where we use the negative of the number of out-of-place operations.
              # While that would be true if this was the only part of the cost, it
              # isn't the whole thing. Both 'communicationsCost' and 'cost' occur before
              # this term, and 'cost' is guaranteed to be positive.
              #
              # It is the negative number of out-of-place operations we use here as
              # FFTW is faster for out-of-place operations than in-place operations for
              # typical transform sizes
              newCost[3] -= 1 # Minus the number of out-of-place operations
            
            # Multiply the costMultiplier through the cost listed by the transform
            newCost[0:2] = [costMultiplier * transformation.get(key, 0) for key in ['communicationsCost', 'cost']]
            newCost[2] += 1 # Number of steps
            # Add that cost to the old cost
            newCost = tuple(old + new for old, new in zip(self.cost, newCost))
            
            # Create the new BasisState and add it to the list of nodes reachable from this node.
            newState = BasisState(
              newCost,
              (resultBasis, resultState),
              self.source,
              previous = self.location,
              transformation = (transformID, transformationPair)
            )
            results.append(newState)
        return results
      
    def pathFromBasisToBasis(start, endID, pathInfo):
      """
      Given a dictionary of shortest paths provided by a GeneralisedBidirectional search, determine
      the actual path that connects the basis `start` and the basis `end`.
      """
      # Final state must be net in-place.
      # But we may or may not need scaling
      loc = start
      path = [loc]
      
      while loc:
        path.append(pathInfo[loc].transformations[endID])
        path.append(pathInfo[loc].next[endID])
        loc = pathInfo[loc].next[endID]
      
      path = path[:-2]
      
      return path
    
    def printBasis(basis):
      if isinstance(basis, basestring): return basis
      elif len(basis) == 1:
        return basis[0] if isinstance(basis[0], basestring) else basis[0].canonicalName
      else:
        return '(' + ', '.join(dimRep if isinstance(dimRep, basestring) else dimRep.canonicalName for dimRep in basis) + ')'
    
    
    geometry = self.getVar('geometry')
    representationMap = dict()
    representationMap.update((rep.canonicalName, rep) for dim in geometry.dimensions for rep in dim.representations)
    distributedRepresentations = [rep for dim in geometry.dimensions for rep in dim.representations if rep.hasLocalOffset]
    BasisState.representationMap = representationMap
    
    def basisToDimRepBasis(repNameBasis):
      if not isinstance(repNameBasis, tuple):
        repNameBasis = tuple([repNameBasis])
      return tuple(representationMap[dimRepName] for dimRepName in repNameBasis)
    
    vectors = set([v for v in self.getVar('templates') if isinstance(v, VectorElement) and v.needsTransforms])
    
    driver = self._driver
    transformMap = dict()
    
    basesFieldMap = dict()
    for vector in vectors:
      vectorBases = vector.basesNeeded.copy()
      if not vector.field.name in basesFieldMap:
        basesFieldMap[vector.field.name] = set()
      basesFieldMap[vector.field.name].update(vectorBases)
    
    # Next step: Perform Dijkstra search over the provided transforms to find the optimal transform map.
    for basesNeeded in basesFieldMap.values():
      targetStates = [BasisState( (0, 0, 0, 0), (basis, BasisState.IN_PLACE), sourceID) for sourceID, basis in enumerate(basesNeeded)]
      targetLocations = [state.location for state in targetStates]
      pathInfo = GeneralisedBidirectionalSearch.perform(targetStates)
      for sourceLoc, targetLoc in combinations(2, targetLocations):
        path = pathFromBasisToBasis(sourceLoc, targetLocations.index(targetLoc), pathInfo)
        # While we now have the paths and we have them quickly, we just need to add the scaling operations
        # where and if needed.
        
        transformMap[frozenset([sourceLoc[0], targetLoc[0]])] = path
    
    self.availableTransformations.append(self.ipMultiply)
    ipMultiplyID = self.availableTransformations.index(self.ipMultiply)
    self.availableTransformations.append(self.oopMultiply)
    oopMultiplyID = self.availableTransformations.index(self.oopMultiply)
    
    for basisPair, path in transformMap.items():
      if any([self.availableTransformations[transformID].get('requiresScaling', False) for transformID, transformPair in path[1::2]]):
        # Scaling is needed.
        # There are different strategies for dealing with this.
        # A good method would be to modify a matrix transform if we can get away with it, but that's an advanced optimisation
        # that will be considered later.
        # A simple optimisation is to use an out-of-place multiply instead of an out-of-place copy
        if self.oopCopy in path:
          # Change an out-of-place copy to an out-of-place multiply if we have one
          path[path.index(self.oopCopy)] = (oopMultiplyID, ())
        else:
          # Add an in-place multiply at the end
          path.extend([(ipMultiplyID, ()), path[-1]])
    
    self.vectorTransformMap = dict()
    transformsNeeded = list()
    basesNeeded = set()
    
    prefixLatticeStringMap = dict()
    postfixLatticeStringMap = dict()
    
    delayedException = None
    
    for vector in vectors:
      basesNeeded.update(vector.basesNeeded)
      vectorBases = list(vector.basesNeeded)
      vectorBases.sort()
      self.vectorTransformMap[vector] = dict(
        bases = vectorBases,
        basisPairMap = dict(),
      )
      vector.transformMap = self.vectorTransformMap[vector]
      
      for basisPair in combinations(2, vectorBases):
        basisPairSet = frozenset(basisPair)
        path = transformMap[basisPairSet]
        
        basisPair = (path[0][0], path[-1][0])
        
        basisPairInfo = dict(
          basisPair = basisPair,
          forwardScale = [],
          backwardScale = [],
        )
        self.vectorTransformMap[vector]['basisPairMap'][basisPairSet] = basisPairInfo
        
        transformSteps = []
        
        for (currentBasis, basisState), (transformID, transformPair) in zip(path[:-2:2], path[1::2]):
          # The transform may decide that different actions of the same transform
          # should be considered different transformations
          # (think FFT's with different numbers of points not in the FFT dimension)
          geometrySpecification = None
          transformation = self.availableTransformations[transformID]
          transformation.setdefault('vectors', set()).add(vector)
          
          resultBasis, (prefixBasis, matchedSourceBasis, postfixBasis) = transformedBasis(currentBasis, transformPair)
          forward = True
          if transformPair:
            sourceBasis = transformPair[0]
            if not isinstance(sourceBasis, tuple): sourceBasis = tuple([sourceBasis])
            forward = True if sourceBasis == matchedSourceBasis else False
          
          if 'requiresScaling' in transformation:
            forwardScale, backwardScale = transformation['forwardScale'], transformation['backwardScale']
            if not forward:
              forwardScale, backwardScale = backwardScale, forwardScale
            basisPairInfo['forwardScale'].append(forwardScale)
            basisPairInfo['backwardScale'].append(backwardScale)
          
          prefixDimReps = basisToDimRepBasis(prefixBasis)
          postfixDimReps = basisToDimRepBasis(postfixBasis)
          
          runtimePrefixDimensions = tuple([dimRep.localLattice for dimRep in prefixDimReps if dimRep.hasLocalOffset or isinstance(dimRep.runtimeLattice, basestring)])
          runtimePostfixDimensions = tuple([dimRep.localLattice for dimRep in postfixDimReps if dimRep.hasLocalOffset or isinstance(dimRep.runtimeLattice, basestring)])
          
          prefixLattice = [(dimRep.latticeEstimate, dimRep.localLattice) for dimRep in prefixDimReps if not (dimRep.hasLocalOffset or isinstance(dimRep.runtimeLattice, basestring))]
          
          postfixLattice = [(dimRep.latticeEstimate, dimRep.localLattice) for dimRep in postfixDimReps if not (dimRep.hasLocalOffset or isinstance(dimRep.runtimeLattice, basestring))]
          postfixLattice.append((vector.nComponents, '_' + vector.id + '_ncomponents'))
          
          if transformation.get('transformType', 'real') is 'real' and vector.type == 'complex':
            postfixLattice.append((2, '2'))
          
          if transformation.get('transformType', 'real') is 'complex' and vector.type == 'real':
            delayedException = ParserException(
              vector.xmlElement,
              "Vector '%(vectorName)s' is of type 'real', but is needed in the following bases: %(basisList)s.\n"
              "To transform between these bases, it is necessary to perform the %(firstBasis)s <--> %(secondBasis)s transform, "
              "which is only possible for complex-valued vectors." % dict(
                vectorName = vector.name,
                basisList = ', '.join([printBasis(basis) for basis in vectorBases]),
                firstBasis = printBasis(transformPair[0]),
                secondBasis = printBasis(transformPair[1])
              )
            )
            # Ideally, we'd rather raise this error on a user-created vector. Similar
            # errors may also exist for related vectors which are of the same type as the original vector
            # Identifying the error as originating from a user-generated vector makes the problem more obvious
            # to the user. The difference between a user-created vector and an automatically generated one is that
            # a user-created vector will have an XML element associated with it.
            # But, should we not find a user-created vector with this problem, the exception will still be raised below.
            # The problem will be harder to trace though.
            if vector.xmlElement:
              raise delayedException
          
          if transformation.get('geometryDependent', False):
            geometrySpecification = (
              runtimePrefixDimensions,
              reduce(operator.mul, [lattice[0] for lattice in prefixLattice], 1),
              reduce(operator.mul, [lattice[0] for lattice in postfixLattice], 1),
              runtimePostfixDimensions
            )
          
          transformDescriptor = (transformID, geometrySpecification, tuple(basisToDimRepBasis(b) for b in transformPair))
          if transformDescriptor not in transformsNeeded:
            transformsNeeded.append(transformDescriptor)
          
          prefixLatticeStrings = list(runtimePrefixDimensions)
          prefixLatticeStrings.extend([lattice[1] for lattice in prefixLattice])
          postfixLatticeStrings = list(runtimePostfixDimensions)
          postfixLatticeStrings.extend([lattice[1] for lattice in postfixLattice])
          
          prefixLatticeString = ' * '.join(prefixLatticeStrings) or '1'
          postfixLatticeString = ' * '.join(postfixLatticeStrings) or '1'
          
          if transformation.get('geometryDependent', False):
            prefixLatticeStringMap.setdefault(transformDescriptor, prefixLatticeString)
            postfixLatticeStringMap.setdefault(transformDescriptor, postfixLatticeString)
          
          transformSteps.append(
            (
              transformsNeeded.index(transformDescriptor),
              forward,
              transformation.get('outOfPlace', False),
              prefixLatticeString,
              postfixLatticeString,
            )
          )
        basisPairInfo['transformSteps'] = transformSteps
    
    # If we still have a delayed exception, we must raise it.
    if delayedException: raise delayedException
    
    # Now we need to extract the transforms and include that information in choosing transforms
    # One advantage of this method is that we no longer have to make extra fft plans or matrices when we could just re-use others.
    # Not only do we need to extract the transforms, but we must also produce a simple list of transforms that must be applied
    # to change between any bases for this vector.
    
    self.basesNeeded = list(basesNeeded)
    self.basesNeeded.sort()
    
    self.neededTransformations = []
    for transformDescriptor in transformsNeeded:
      transformID, transformSpecifier, transformPair = transformDescriptor
      transformation = self.availableTransformations[transformID].copy()
      transformation['transformSpecifier'] = transformSpecifier
      del transformation['transformations']
      transformation['transformPair'] = transformPair
      # A bit dodgy, but I can't think of a better way
      if transformation.get('geometryDependent', False):
        transformation['prefixLatticeString'] = prefixLatticeStringMap[transformDescriptor]
        transformation['postfixLatticeString'] = postfixLatticeStringMap[transformDescriptor]
      self.neededTransformations.append(transformation)
    
    def functionImplementation(func):
      transform = func.transform
      transformFunction = transform.get('transformFunction')
      transformFunctionPrelude = "if (_prefix_lattice <= 0 || _postfix_lattice <= 0) return;\n"
      return transformFunctionPrelude + transformFunction(*func.transformFunctionArgs) if transformFunction else ''
    
    for tID, transform in enumerate(self.neededTransformations):
      description = transform.get('description')
      if transform['transformPair'] and not description:
        basisA, basisB = transform['transformPair']
        description = "%s <---> %s transform" % (printBasis(basisA), printBasis(basisB))
        transform['description'] = description
      functionName = '_transform_%i' % tID
      args = [
        ('bool', '_forward'),
        ('real', '_multiplier'),
        ('real* const __restrict__', '_data_in'),
        ('real* const __restrict__', '_data_out'),
        ('ptrdiff_t', '_prefix_lattice'),
        ('ptrdiff_t', '_postfix_lattice')
      ]
      f = Function(name = functionName,
                   args = args,
                   implementation = functionImplementation,
                   description = description)
      f.transform = transform
      f.transformFunctionArgs = [tID, transform, f]
      self.functions[functionName] = f
      transform['owner'].transformations.append((tID, transform))
  

