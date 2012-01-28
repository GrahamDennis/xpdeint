#!/usr/bin/env python
# encoding: utf-8
"""
Utilities.py

Created by Graham Dennis on 2008-09-15.

Copyright (c) 2008-2012, Graham Dennis

All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
    * Neither the name of The Australian National University nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

from xpdeint.ParserException import ParserException
import re
import sys

from heapq import heapify, heappush, heappop
import operator

class lazy_property(object):
  """
  A data descriptor that provides a default value for the attribute
  represented via a user-defined function, and this function is evaluated
  at most once with the result cached. Additionally, the property can be
  overridden.
  """
  
  def __init__(self, fget, doc=None):
    self.fget = fget
    self.__doc__ = doc
    if not self.__doc__:
      self.__doc__ = fget.__doc__
    self.__name__ = fget.__name__
  
  def __get__(self, obj, objtype=None):
    if obj is None:
      return self
    if self.fget is None:
      raise AttributeError, "unreadable attribute"
    result = obj.__dict__[self.__name__] = self.fget(obj)
    return result
  

def valueForKeyPath(base, keyPath):
  """
  Return the value for a dotted-name lookup of `keyPath` anchored at `base`.

  This is similar to the KVC methods in Objective-C, however its use is appropriate in Python.
  Evaluating the `keyPath` 'foo.bar.baz' returns the object that would be returned by evaluating
  the string (in Python) base.foo.bar.baz
  """
  attrNames = keyPath.split('.')
  try:
    currentObject = base
    for attrName in attrNames:
      if isinstance(currentObject, dict):
        # Access via dictionary key
        currentObject = currentObject[attrName]
      else:
        # Access attribute
        currentObject = getattr(currentObject, attrName)
  except Exception, err:
    baseRep = repr(base)
    print >> sys.stderr, "Hit exception trying to get keyPath '%(keyPath)s' on object %(baseRep)s." % locals()
    raise
  return currentObject

def setValueForKeyPath(base, value, keyPath):
  """Set the value of the result of the dotted-name lookup of `keyPath` anchored at `base` to `value`."""
  attrNames = keyPath.split('.')
  lastAttrName = attrNames.pop()
  currentObject = base
  try:
    for attrName in attrNames:
      currentObject = getattr(currentObject, attrName)
    if isinstance(currentObject, dict):
      # Set dictionary entry
      currentObject[lastAttrName] = value
    else:
      # Set attribute
      setattr(currentObject, lastAttrName, value)
  except Exception, err:
    baseRep = repr(base)
    print >> sys.stderr, "Hit exception trying to set keyPath '%(keyPath)s' on object %(baseRep)s." % locals()
    raise


def greatestCommonFactor(num):
    num = [n for n in num if n > 0]
    t_val = num[0]
    for cnt in range(len(num)-1):
        num1 = t_val
        num2 = num[cnt+1]
        if num1 < num2:
            num1,num2=num2,num1
        while num1 - num2:
            num3 = num1 - num2
            num1 = max(num2,num3)
            num2 = min(num2,num3)
        t_val = num1
    return t_val

def leastCommonMultiple(num):
    num = [n for n in num if n > 0]
    if len(num) == 0:
        return 1
    t_val = num[0]
    for cnt in range(len(num)-1):
        num1 = t_val
        num2 = num[cnt+1]
        tmp = greatestCommonFactor([num1,num2])
        t_val = tmp * num1/tmp * num2/tmp
    return t_val

protectedNamesSet = set("""
gamma nan ceil floor trunc round remainder abs sqrt hypot
exp log pow cos sin tan cosh sinh tanh acos asin atan
j0 j1 jn y0 y1 yn erf real complex Re Im mod2 integer mod
""".split())

def symbolsInString(string, xmlElement = None):
    wordRegex = re.compile(r'\b\w+\b')
    symbolRegex = re.compile(r'[a-zA-Z]\w*')
    words = wordRegex.findall(string)
    for word in words:
        if not symbolRegex.match(word):
            raise ParserException(
                xmlElement,
                "'%(word)s' is not a valid name. All names must start with a letter, "
                "after that letters, numbers and underscores ('_') may be used." % locals()
            )
        if word in protectedNamesSet:
            raise ParserException(
                xmlElement,
                "'%(word)s' cannot be used as a name because it conflicts with an internal function or variable of the same name. "
                "Choose another name." % locals()
            )
    return words

def symbolInString(string, xmlElement = None):
    words = symbolsInString(string, xmlElement)
    if len(words) > 1:
        raise ParserException(
            xmlElement,
            "Only one name was expected at this point. The problem was with the string '%(string)s'" % locals()
        )
    if words:
        return words[0]
    else:
        return None
    

def unique(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result

def permutations(*iterables):
    def permuteTwo(it1, it2):
        for o1 in it1:
            for o2 in it2:
                if isinstance(o1, tuple):
                    yield o1 + (o2,)
                else:
                    yield (o1, o2)
    
    if len(iterables) == 1:
        return iterables[0]
    
    it = iterables[0]
    for it2 in iterables[1:]:
        it = permuteTwo(it, it2)
    
    return it

def combinations(itemCount, *lsts):
    """Generator for all unique combinations of each list in `lsts` containing `itemCount` elements."""
    def _combinations(itemCount, lst):
        if itemCount == 0 or itemCount > len(lst):
            return
        if itemCount == 1:
            for o in lst:
                yield (o,)
        elif itemCount == len(lst):
            yield tuple(lst)
        else:
            if not isinstance(lst, list):
              lst = list(lst)
            for o in _combinations(itemCount-1, lst[1:]):
                yield (lst[0],) + o
            for o in _combinations(itemCount, lst[1:]):
                yield o
    if len(lsts) == 1:
        return _combinations(itemCount, lsts[0])
    iterables = [list(_combinations(itemCount, lst)) for lst in lsts]
    return permutations(*iterables)


class GeneralisedBidirectionalSearch(object):
    """
    A Generalised bidirectional search is an algorithm to search for the least-cost
    route between a subset of nodes in a graph.
    
    Typically, only one of the least-cost solutions are desired, however
    as we will have some additional criteria to apply later to the returned
    paths, this implementation returns all of the least-cost paths between
    two nodes.
    """
    class State(object):
        """
        A helper class to store information about a given node, the cost to get there
        and the step that was used to get to this node.
        
        It is intended that this class be subclassed for use in searches.
        """
        __slots__ = ['cost', 'location', 'previous', 'source', 'transformation']
        def __init__(self, cost, location, source, previous = None, transformation = None):
            self.cost = cost
            self.location = location
            self.source = source
            self.previous = previous
            self.transformation = transformation
        
        def next(self):
            """
            This function is to return the nodes reachable from this node, the costs and
            some related information.
            
            This function must be implemented by a subclass.
            """
            assert False
        
    
    class NodeInfo(object):
        """
        This helper class stores the information known about the minimum-cost
        routes to the target nodes from a given node. This information includes the minimum cost
        to reach the target nodes and the next step towards each target node.
        """
        __slots__ = ['costs', 'next', 'transformations']
        def __init__(self, sourceIdx, cost, next = None, transformation = None):
            self.costs = [None] * GeneralisedBidirectionalSearch.NodeInfo.targetCount
            self.next = self.costs[:]
            self.transformations = self.costs[:]
            self.costs[sourceIdx] = cost
            self.next[sourceIdx] = next
            self.transformations[sourceIdx] = transformation
        
    @staticmethod
    def perform(targetNodes):
        """
        This function performs the 'bidirectional' search between the nodes `targetNodes`
        This information is returned in a dictionary that
        maps a given node to a `NodeInfo` object that contains information about
        the minimum-cost routes to reach that node.
        """
        targetLocations = [node.location for node in targetNodes]
        queue = [(node.cost, node) for node in targetNodes]
        heapify(queue)
        GeneralisedBidirectionalSearch.NodeInfo.targetCount = len(targetNodes)
        pathInfo = dict()
        targetRoutes = dict()
        
        maxCost = None
        
        # This algorithm works by iterating over a queue considering paths in
        # order of increasing cost. As a path is considered, every possible
        # single-step extension to this path is considered and added to the queue.
        # Eventually the queue empties when the only paths contained are more expensive
        # versions of paths that have already been considered.
        #
        # But we don't have to wait for the queue to empty, we can stop whenever we know how to get between
        # each of our targetNodes
        
        def processState(state):
            for nextState in state.next():
                if nextState.location in pathInfo \
                    and pathInfo[nextState.location].costs[nextState.source] is not None:
                    continue
                heappush(queue, (nextState.cost, nextState))
        
        def costsOperation(op, A, B):
          return tuple(op(a, b) for a, b in zip(A, B))
        
        while queue:
            currentState = heappop(queue)[1]
            if maxCost is not None and currentState.cost > maxCost: break
            if not currentState.location in pathInfo:
                # This location hasn't been reached. Add a NodeInfo object to pathInfo
                pathInfo[currentState.location] = GeneralisedBidirectionalSearch.NodeInfo(
                    currentState.source,
                    currentState.cost,
                    currentState.previous,
                    currentState.transformation,
                )
                if currentState.location in targetLocations \
                    and not currentState.source == targetLocations.index(currentState.location) \
                    and not frozenset([currentState.source, targetLocations.index(currentState.location)]) in targetRoutes:
                    targetRoutes[frozenset([currentState.source, targetLocations.index(currentState.location)])] = currentState.cost
                    maxCost = max(currentState.cost, maxCost)
                processState(currentState)
            elif pathInfo[currentState.location].costs[currentState.source] is None \
                or pathInfo[currentState.location].costs[currentState.source] > currentState.cost:
                # While this location has been reached before, it hasn't been reached from this source
                # or it has been reached, but with a higher cost.
                
                nodeInfo = pathInfo[currentState.location]
                nodeInfo.costs[currentState.source] = currentState.cost
                nodeInfo.next[currentState.source] = currentState.previous
                nodeInfo.transformations[currentState.source] = currentState.transformation
                
                # If we have reached a location which itself is reachable from a different targetNode,
                # then we have found a shortest route from our source to the targetNode (and vice-versa)
                for destination, destCost in enumerate(nodeInfo.costs):
                    if destCost is None \
                        or not frozenset([currentState.source, destination]) in targetRoutes \
                        or targetRoutes[frozenset([currentState.source, destination])] < destCost + currentState.cost \
                        or destination == currentState.source:
                        continue
                    
                    # The total cost for the route
                    totalCost = costsOperation(operator.add, destCost, currentState.cost)
                    targetRoutes[frozenset([currentState.source, destination])] = currentState.cost
                    maxCost = max(currentState.cost, maxCost)
                    
                    # Now that we have found two intersecting routes, we must update each part with
                    # the cost and path information to the corresponding targets
                    
                    forwardBackwardPathUpdateInfo = [
                      (currentState.location, currentState.previous, currentState.source, destination),
                      (currentState.previous, currentState.location, destination, currentState.source)
                    ]
                    
                    for loc, prev, source, dest in forwardBackwardPathUpdateInfo:
                        transformation = currentState.transformation
                        while loc is not None:
                            nodeInfo = pathInfo[loc]
                            cost = costsOperation(operator.sub, totalCost, nodeInfo.costs[dest])
                            nodeInfo.costs[source] = cost
                            nodeInfo.next[source] = prev
                            nodeInfo.transformations[source] = transformation
                            processState(currentState.__class__(cost, loc, source, prev, transformation))
                            prev, loc = loc, nodeInfo.next[dest]
                            transformation = nodeInfo.transformations[dest]
                    
                processState(currentState)
        return pathInfo
    
