#############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

__version__='$Revision: 1.8 $'[11:-2]

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
        mtype = type(module)
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
        except Unauthorized:
            raise ImportError, ('import of "%s" from "%s" is unauthorized'
                                % (name, mname))
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
