#!/usr/bin/env python
# encoding: utf-8
"""
_TransformMultiplexer.py

Created by Graham Dennis on 2008-12-23.
Copyright (c) 2008 __MyCompanyName__. All rights reserved.
"""

from xpdeint.Features._Feature import _Feature
from xpdeint.Utilities import lazy_property

class _TransformMultiplexer (_Feature):
  featureName = 'TransformMultiplexer'
  transformClasses = dict()
  
  def __init__(self, *args, **KWs):
    _Feature.__init__(self, *args, **KWs)
    self.transforms = set()
  
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
      return cls(parent = self.getVar('simulation'), **self.argumentsToTemplateConstructors)
  
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
    
  

