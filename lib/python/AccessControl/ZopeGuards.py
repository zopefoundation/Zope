#############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

__version__='$Revision: 1.12 $'[11:-2]

from RestrictedPython.Guards import safe_builtins, _full_read_guard, \
     full_write_guard
from RestrictedPython.Utilities import utility_builtins
from SecurityManagement import getSecurityManager
from SecurityInfo import secureModule
from SimpleObjectPolicies import Containers
from zExceptions import Unauthorized

_marker = []  # Create a new marker object.

safe_builtins = safe_builtins.copy()
safe_builtins.update(utility_builtins)

try:

    #raise ImportError
    import os
    if os.environ.get("ZOPE_SECURITY_POLICY", None) == "PYTHON":
        raise ImportError # :)
    from cAccessControl import aq_validate, guarded_getattr

except ImportError:

    def aq_validate(inst, obj, name, v, validate):
        return validate(inst, obj, name, v)


    def guarded_getattr(inst, name, default=_marker):
        if name[:1] != '_':
            # Try to get the attribute normally so that unusual
            # exceptions are caught early.
            try: v = getattr(inst, name)
            except AttributeError:
                if default is not _marker:
                    return default
                raise
            if Containers(type(inst)):
                # Simple type.  Short circuit.
                return v
            validate = getSecurityManager().validate
            # Filter out the objects we can't access.
            if hasattr(inst, 'aq_acquire'):
                return inst.aq_acquire(name, aq_validate, validate)
            # Or just try to get the attribute directly.
            if validate(inst, inst, name, v):
                return v
        raise Unauthorized, name

safe_builtins['getattr'] = guarded_getattr

def guarded_hasattr(object, name):
    try:
        guarded_getattr(object, name)
    except (AttributeError, Unauthorized):
        return 0
    return 1
safe_builtins['hasattr'] = guarded_hasattr

SliceType = type(slice(0))
def guarded_getitem(object, index):
    if type(index) is SliceType:
        if index.step is not None:
            v = object[index]
        else:
            start = index.start
            stop = index.stop
            if start is None:
                start = 0
            if stop is None:
                v = object[start:]
            else:
                v = object[start:stop]
        # We don't guard slices.
        return v
    v = object[index]
    if Containers(type(object)) and Containers(type(v)):
        # Simple type.  Short circuit.
        return v
    if getSecurityManager().validate(object, object, index, v):
        return v
    raise Unauthorized, 'unauthorized access to element %s' % `i`


full_read_guard = _full_read_guard(guarded_getattr, guarded_getitem)


def guarded_filter(f, seq, skip_unauthorized=0):
    if type(seq) is type(''):
        return filter(f, seq)
    if f is None:
        def f(x): return x
    v = getSecurityManager().validate
    result = []
    a = result.append
    for el in seq:
        if v(seq, seq, None, el):
            if f(el): a(el)
        elif not skip_unauthorized:
            raise Unauthorized, 'unauthorized access to element'
    return result
safe_builtins['filter'] = guarded_filter

def guarded_map(f, *seqs):
    safe_seqs = []
    for seqno in range(len(seqs)):
        seq = guarded_getitem(seqs, seqno)
        safe_seqs.append(seq)
    return map(f, *safe_seqs)
safe_builtins['map'] = guarded_map

import sys
def guarded_import(mname, globals={}, locals={}, fromlist=None):
    mnameparts = mname.split('.')
    firstmname = mnameparts[0]
    validate = getSecurityManager().validate
    module = load_module(None, None, mnameparts, validate, globals, locals)
    if module is not None:
        if fromlist is None:
            fromlist = ()
        try:
            for name in fromlist:
                if name == '*':
                    raise ImportError, ('"from %s import *" is not allowed'
                                        % mname)
                v = getattr(module, name, None)
                if v is None:
                    v = load_module(module, mname, [name], validate,
                                    globals, locals)
                if not validate(module, module, name, v):
                    raise Unauthorized
            else:
                return __import__(mname, globals, locals, fromlist)
        except Unauthorized, why:
            raise ImportError, ('import of "%s" from "%s" is unauthorized. %s'
                                % (name, mname, why))
    raise ImportError, 'import of "%s" is unauthorized' % mname
safe_builtins['__import__'] = guarded_import

def load_module(module, mname, mnameparts, validate, globals, locals):
    modules = sys.modules
    while mnameparts:
        nextname = mnameparts.pop(0)
        if mname is None:
            mname = nextname
        else:
            mname = '%s.%s' % (mname, nextname)
        nextmodule = modules.get(mname, None)
        if nextmodule is None:
            nextmodule = secureModule(mname, globals, locals)
            if nextmodule is None:
                return
        else:
            secureModule(mname)
        if module and not validate(module, module, nextname, nextmodule):
            return
        module = nextmodule
    return module
