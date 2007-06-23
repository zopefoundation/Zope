#############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import inspect
from zExceptions import Forbidden
from ZPublisher.HTTPRequest import HTTPRequest

_default = []

def _buildFacade(spec, docstring):
    """Build a facade function, matching the decorated method in signature.
    
    Note that defaults are replaced by _default, and _curried will reconstruct
    these to preserve mutable defaults.
    
    """
    args = inspect.formatargspec(formatvalue=lambda v: '=_default', *spec)
    callargs = inspect.formatargspec(formatvalue=lambda v: '', *spec)
    return 'def _facade%s:\n    """%s"""\n    return _curried%s' % (
        args, docstring, callargs)

def postonly(callable):
    """Only allow callable when request method is POST."""
    spec = inspect.getargspec(callable)
    args, defaults = spec[0], spec[3]
    try:
        r_index = args.index('REQUEST')
    except ValueError:
        raise ValueError('No REQUEST parameter in callable signature')
    
    arglen = len(args)
    if defaults is not None:
        defaults = zip(args[arglen - len(defaults):], defaults)
        arglen -= len(defaults)
            
    def _curried(*args, **kw):
        request = None
        
        if len(args) > r_index:
            request = args[r_index]
        if isinstance(request, HTTPRequest):
            if request.get('REQUEST_METHOD', 'GET').upper() != 'POST':
                raise Forbidden('Request must be POST')
        
        # Reconstruct keyword arguments
        if defaults is not None:
            args, kwparams = args[:arglen], args[arglen:]
            for positional, (key, default) in zip(kwparams, defaults):
                if positional is _default:
                    kw[key] = default
                else:
                    kw[key] = positional

        return callable(*args, **kw)
    
    # Build a facade, with a reference to our locally-scoped _curried
    facade_globs = dict(_curried=_curried, _default=_default)
    exec _buildFacade(spec, callable.__doc__) in facade_globs
    return facade_globs['_facade']

__all__ = ('postonly',)
