##############################################################################
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
__version__='$Revision: 1.5 $'[11:-2]

"""BeforeTraverse interface and helper classes"""

# Interface

def registerBeforeTraverse(container, object, app_handle, priority=99):
    """Register an object to be called before a container is traversed.

    'app_handle' should be a string or other hashable value that
    distinguishes the application of this object, and which must
    be used in order to unregister the object.

    If the container will be pickled, the object must be a callable class
    instance, not a function or method.

    'priority' is optional, and determines the relative order in which
    registered objects will be called.
    """
    btr = getattr(container, '__before_traverse__', {})
    btr[(priority, app_handle)] = object
    rewriteBeforeTraverse(container, btr)

def unregisterBeforeTraverse(container, app_handle):
    """Unregister a __before_traverse__ hook object, given its 'app_handle'.

    Returns a list of unregistered objects."""
    btr = getattr(container, '__before_traverse__', {})
    objects = []
    for k in btr.keys():
        if k[1] == app_handle:
            objects.append(btr[k])
            del btr[k]
    if objects:
        rewriteBeforeTraverse(container, btr)
    return objects

def queryBeforeTraverse(container, app_handle):
    """Find __before_traverse__ hook objects, given an 'app_handle'.

    Returns a list of (priority, object) pairs."""
    btr = getattr(container, '__before_traverse__', {})
    objects = []
    for k in btr.keys():
        if k[1] == app_handle:
            objects.append((k[0], btr[k]))
    return objects

# Implementation tools

def rewriteBeforeTraverse(container, btr):
    """Rewrite the list of __before_traverse__ hook objects"""
    container.__before_traverse__ = btr
    hookname = '__before_publishing_traverse__'
    dic = hasattr(container.__class__, hookname)
    bpth = container.__dict__.get(hookname, None)
    if isinstance(bpth, MultiHook):
        bpth = bpth._prior
    bpth = MultiHook(hookname, bpth, dic)
    setattr(container, hookname, bpth)
    
    keys = btr.keys()
    keys.sort()
    for key in keys:
        bpth.add(btr[key])

class MultiHook:
    """Class used to multiplex hook.

    MultiHook calls the named hook from the class of the container, then
    the prior hook, then all the hooks in its list.
    """
    def __init__(self, hookname, prior, defined_in_class):
        self._hookname = hookname
        self._prior = prior
        self._defined_in_class = defined_in_class
        self._list = []

    def __call__(self, container, request):
        if self._defined_in_class:
            # Assume it's an unbound method
            getattr(container.__class__, self._hookname)(container, request)
        prior = self._prior
        if prior is not None:
            prior(container, request)
        for cob in self._list:
            cob(container, request)

    def add(self, cob):
        self._list.append(cob)

# Helper class

class NameCaller:
    """Class used to proxy sibling objects by name.

    When called with a container and request object, it gets the named
    attribute from the container and calls it.  If the name is not
    found, it fails silently.

    >>> registerBeforeTraverse(folder, NameCaller('preop'), 'XApp')
    """

    def __init__(self, name):
        self.name = name

    def __call__(self, container, request):
        try:
            meth = getattr(container, self.name)
        except AttributeError:
            return

        args = getattr(getattr(meth, 'func_code', None), 'co_argcount', 2)
        try:
            apply(meth, (container, request, None)[:args])
        except:
            from zLOG import LOG, ERROR
            import sys
            LOG('BeforeTraverse', ERROR,
                'Error while invoking hook: "%s"' % self.name, error=
                sys.exc_info())
