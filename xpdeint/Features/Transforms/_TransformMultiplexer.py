#!/usr/bin/env python
# encoding: utf-8
"""
_TransformMultiplexer.py

Created by Graham Dennis on 2008-12-23.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature
from xpdeint.Utilities import lazy_property, combinations, GeneralisedBidirectionalSearch
from xpdeint.Function import Function

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
  
  def transformsForVector(self, vector):
    return set([dim.transform for dim in vector.field.dimensions if dim.transform.hasattr('goSpaceFunctionContentsForVector')])
  
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
    try:
      attr = _Feature.__getattribute__(self, name)
    except AttributeError, err:
      # If the attribute name is not in the list of functions we want to proxy
      # then re-raise the exception
      if not name in ['mainBegin', 'mainEnd']: raise
      # We don't have the attribute, so maybe one of our child transforms does
      transforms = _Feature.__getattribute__(self, 'transforms')
      childAttributes = [getattr(t, name) for t in transforms if t.hasattr(name)]
      # No child has the transform, re-raise the exception
      if not childAttributes: raise
      # A child has the attribute. Check they are all callable. If not, don't multiplex
      # This line is here for debugging only
      # assert all([callable(ca) for ca in childAttributes]), "Tried to multiplex call to non-callable attribute '%(name)s'" % locals()
      if not all([callable(ca) for ca in childAttributes]): raise
      
      if len(childAttributes) == 1:
        return childAttributes[0]
      
      # Create the function that does the actual multiplexing
      def multiplexingFunction(*args, **KWs):
        results = [ca(*args, **KWs) for ca in childAttributes]
        return ''.join([result for result in results if result is not None])
      
      return multiplexingFunction
    else:
      return attr
    
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
        
        # FIXME: Dodgy hack that can be removed when 'distributed y' has a dimRep
        missingRepNames = [repName for repName in currentBasis if not repName in self.representationMap]
        for missingRepName in missingRepNames:
          if missingRepName.startswith('distributed '):
            self.representationMap[missingRepName] = self.representationMap[missingRepName[len('distributed '):]]
          else:
            self.representationMap[missingRepName] = self.representationMap['distributed ' + missingRepName]
        
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
              [self.representationMap[repName].lattice \
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
              newCost[3] += 1 # Number of out-of-place operations
            
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
    
    
    def convertSpaceInFieldToBasis(space, field):
      """Transforms an old-style `space` in field `field` to a new-style basis specification."""
      return tuple(dim.inSpace(space).name for dim in field.dimensions)
    
    geometry = self.getVar('geometry')
    representationMap = dict()
    representationMap.update((rep.canonicalName, rep) for dim in geometry.dimensions for rep in dim.representations)
    distributedRepresentations = [rep for dim in geometry.dimensions for rep in dim.representations if rep.hasLocalOffset]
    BasisState.representationMap = representationMap
    
    def basisToDimRepBasis(repNameBasis):
      if not isinstance(repNameBasis, tuple):
        repNameBasis = tuple([repNameBasis])
      return tuple(representationMap[dimRepName] for dimRepName in repNameBasis)
    
    vectors = [v for v in self.getVar('simulationVectors') if v.needsTransforms]
    driver = self._driver
    transformMap = dict()
    
    basesFieldMap = dict()
    for vector in vectors:
      vectorBases = set(driver.canonicalBasisForBasis(convertSpaceInFieldToBasis(space, vector.field))
                          for space in vector.spacesNeeded)
      if not vector.field.name in basesFieldMap:
        basesFieldMap[vector.field.name] = set()
      basesFieldMap[vector.field.name].update(vectorBases)
    
    # Next step: Perform Dijkstra search over the provided transforms to find the optimal transform map.
    for basesNeeded in basesFieldMap.values():
      targetStates = [BasisState( (0, 0, 0, 0), (basis, BasisState.IN_PLACE), sourceID) for sourceID, basis in enumerate(basesNeeded)]
      targetLocations = [state.location for state in targetStates]
      print targetLocations
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
      print basisPair, path
    
    self.vectorTransformMap = dict()
    transformsNeeded = list()
    
    for vector in vectors:
      vectorBases = list(set(driver.canonicalBasisForBasis(convertSpaceInFieldToBasis(space, vector.field))
                                for space in vector.spacesNeeded))
      vectorBases.sort()
      self.vectorTransformMap[vector] = dict(
        bases = vectorBases,
        basisPairMap = dict(),
      )
      
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
          if 'requiresScaling' in transformation:
            basisPairInfo['forwardScale'].append(transformation['forwardScale'])
            basisPairInfo['backwardScale'].append(transformation['backwardScale'])
          
          resultBasis, (prefixBasis, matchedSourceBasis, postfixBasis) = transformedBasis(currentBasis, transformPair)
          forward = True if transformPair and transformPair[0] == matchedSourceBasis else False
          prefixDimReps = basisToDimRepBasis(prefixBasis)
          postfixDimReps = basisToDimRepBasis(postfixBasis)
          
          mpiPrefix = [dimRep.localLattice for dimRep in prefixDimReps if dimRep.hasLocalOffset]
          
          prefixLattice = [(dimRep.lattice, dimRep.localLattice) for dimRep in prefixDimReps if not dimRep.hasLocalOffset]
          
          postfixLattice = [(dimRep.lattice, dimRep.localLattice) for dimRep in postfixDimReps]
          postfixLattice.append((vector.nComponents, '_' + vector.id + '_ncomponents'))
          
          if transformation.get('transformType', 'real') is 'real' and vector.type == 'complex':
            postfixLattice.append((2, '2'))
          
          if transformation.get('geometryDependent', False):
            geometrySpecification = (
              mpiPrefix,
              reduce(operator.mul, [lattice[0] for lattice in prefixLattice], 1),
              reduce(operator.mul, [lattice[0] for lattice in postfixLattice], 1)
            )
          
          transformDescriptor = (transformID, geometrySpecification, tuple(basisToDimRepBasis(b) for b in transformPair))
          if transformDescriptor not in transformsNeeded:
            transformsNeeded.append(transformDescriptor)
          
          prefixLatticeStrings = mpiPrefix[:]
          prefixLatticeStrings.extend([lattice[1] for lattice in prefixLattice])
          postfixLatticeStrings = [lattice[1] for lattice in postfixLattice]
          
          transformSteps.append(
            (
              transformsNeeded.index(transformDescriptor),
              forward,
              prefixLatticeStrings or ['1'],
              postfixLatticeStrings or ['1'],
            )
          )
        basisPairInfo['transformSteps'] = transformSteps
        print basisPair, transformSteps
    
    # Now we need to extract the transforms and include that information in choosing transforms
    # One advantage of this method is that we no longer have to make extra fft plans or matrices when we could just re-use others.
    # Not only do we need to extract the transforms, but we must also produce a simple list of transforms that must be applied
    # to change between any bases for this vector.
    
    for transformID, transformSpecifier, transformPair in transformsNeeded:
      transformation = self.availableTransformations[transformID].copy()
      transformation['transformSpecifier'] = transformSpecifier
      del transformation['transformations']
      transformation['transformPair'] = transformPair
      self.neededTransformations.append(transformation)
    
    def functionImplementation(func):
      transform = func.transform
      transformFunction = transform.get('transformFunction')
      return transformFunction(*func.transformFunctionArgs) if transformFunction else ''
    
    def printBasis(basis):
      if len(basis) == 1:
        return basis[0].canonicalName
      else:
        return '(' + ', '.join(dimRep.canonicalName for dimRep in basis) + ')'
    
    for tID, transform in enumerate(self.neededTransformations):
      description = transform.get('description')
      if transform['transformPair'] and not description:
        basisA, basisB = transform['transformPair']
        description = "%s <---> %s transform" % (printBasis(basisA), printBasis(basisB))
        transform['description'] = description
      functionName = '_transform_%i' % tID
      args = [
        ('bool', '_forward'),
        ('double', '_multiplier'),
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
  

