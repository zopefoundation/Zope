##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Page Template Expression Engine

Page Template-specific implementation of TALES, with handlers
for Python expressions, string literals, and paths.

$Id$
"""
import re, sys
from TALES import Engine, CompilerError, NAME_RE, Undefined, Default
from TALES import _parse_expr, _valid_name
from Acquisition import aq_base, aq_inner, aq_parent
from DeferExpr import LazyWrapper, LazyExpr
from zope.tales.expressions import DeferWrapper, DeferExpr, StringExpr, NotExpr

# BBB 2005/05/01 -- remove after 12 months
import zope.deferredimport
zope.deferredimport.deprecatedFrom(
    "Use the Zope 3 ZPT engine instead of the Zope 2 one.  Expression "
    "types can be imported from zope.tales.expressions.  This reference "
    "will be gone in Zope 2.12.",
    "zope.tales.expressions",
    "StringExpr", "NotExpr"
    )

_engine = None
def getEngine():
    global _engine
    if _engine is None:
       from PathIterator import Iterator
       _engine = Engine(Iterator)
       installHandlers(_engine)
    return _engine

def installHandlers(engine):
    reg = engine.registerType
    pe = PathExpr
    for pt in ('standard', 'path', 'exists', 'nocall'):
        reg(pt, pe)
    reg('string', StringExpr)
    reg('python', PythonExpr)
    reg('not', NotExpr)
    reg('defer', DeferExpr)
    reg('lazy', LazyExpr)

import AccessControl
import AccessControl.cAccessControl
acquisition_security_filter = AccessControl.cAccessControl.aq_validate
from AccessControl import getSecurityManager
from AccessControl.ZopeGuards import guarded_getattr
from AccessControl import Unauthorized
from ZRPythonExpr import PythonExpr
from ZRPythonExpr import _SecureModuleImporter
from ZRPythonExpr import call_with_ns

SecureModuleImporter = _SecureModuleImporter()

Undefs = (Undefined, AttributeError, KeyError,
          TypeError, IndexError, Unauthorized)

def render(ob, ns):
    """
    Calls the object, possibly a document template, or just returns it if
    not callable.  (From DT_Util.py)
    """
    if hasattr(ob, '__render_with_namespace__'):
        ob = call_with_ns(ob.__render_with_namespace__, ns)
    else:
        base = aq_base(ob)
        if callable(base):
            try:
                if getattr(base, 'isDocTemp', 0):
                    ob = call_with_ns(ob, ns, 2)
                else:
                    ob = ob()
            except AttributeError, n:
                if str(n) != '__call__':
                    raise
    return ob

class SubPathExpr:
    def __init__(self, path):
        self._path = path = path.strip().split('/')
        self._base = base = path.pop(0)
        if base and not _valid_name(base):
            raise CompilerError, 'Invalid variable name "%s"' % base
        # Parse path
        self._dp = dp = []
        for i in range(len(path)):
            e = path[i]
            if e[:1] == '?' and _valid_name(e[1:]):
                dp.append((i, e[1:]))
        dp.reverse()

    def _eval(self, econtext,
              list=list, isinstance=isinstance, StringType=type('')):
        vars = econtext.vars
        path = self._path
        if self._dp:
            path = list(path) # Copy!
            for i, varname in self._dp:
                val = vars[varname]
                if isinstance(val, StringType):
                    path[i] = val
                else:
                    # If the value isn't a string, assume it's a sequence
                    # of path names.
                    path[i:i+1] = list(val)
        __traceback_info__ = base = self._base
        if base == 'CONTEXTS' or not base:
            ob = econtext.contexts
        else:
            ob = vars[base]
        if isinstance(ob, DeferWrapper):
            ob = ob()
        if path:
            ob = restrictedTraverse(ob, path, getSecurityManager())
        return ob

class PathExpr:
    def __init__(self, name, expr, engine):
        self._s = expr
        self._name = name
        self._hybrid = 0
        paths = expr.split('|')
        self._subexprs = []
        add = self._subexprs.append
        for i in range(len(paths)):
            path = paths[i].lstrip()
            if _parse_expr(path):
                # This part is the start of another expression type,
                # so glue it back together and compile it.
                add(engine.compile(('|'.join(paths[i:]).lstrip())))
                self._hybrid = 1
                break
            add(SubPathExpr(path)._eval)

    def _exists(self, econtext):
        for expr in self._subexprs:
            try:
                expr(econtext)
            except Undefs:
                pass
            else:
                return 1
        return 0

    def _eval(self, econtext,
              isinstance=isinstance,
              BasicTypes=(str, unicode, dict, list, tuple, bool),
              render=render):
        for expr in self._subexprs[:-1]:
            # Try all but the last subexpression, skipping undefined ones.
            try:
                ob = expr(econtext)
            except Undefs:
                pass
            else:
                break
        else:
            # On the last subexpression allow exceptions through, and
            # don't autocall if the expression was not a subpath.
            ob = self._subexprs[-1](econtext)
            if self._hybrid:
                return ob

        if self._name == 'nocall' or isinstance(ob, BasicTypes):
            return ob
        # Return the rendered object
        return render(ob, econtext.vars)

    def __call__(self, econtext):
        if self._name == 'exists':
            return self._exists(econtext)
        return self._eval(econtext)

    def __str__(self):
        return '%s expression %s' % (self._name, `self._s`)

    def __repr__(self):
        return '%s:%s' % (self._name, `self._s`)

from zope.interface import Interface, implements
from zope.component import queryMultiAdapter
from zope.traversing.interfaces import TraversalError
from zope.traversing.namespace import nsParse, namespaceLookup
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.publisher.browser import setDefaultSkin

class FakeRequest(dict):
    implements(IBrowserRequest)

    def getURL(self):
        return "http://codespeak.net/z3/five"

def restrictedTraverse(object, path, securityManager,
                       get=getattr, has=hasattr, N=None, M=[],
                       TupleType=type(()) ):

    REQUEST = FakeRequest()
    REQUEST['path'] = path
    REQUEST['TraversalRequestNameStack'] = path = path[:] # Copy!
    setDefaultSkin(REQUEST)
    path.reverse()
    validate = securityManager.validate
    __traceback_info__ = REQUEST
    while path:
        name = path.pop()

        if isinstance(name, TupleType):
            object = object(*name)
            continue

        if not name or name[0] == '_':
            # Skip directly to item access
            o = object[name]
            # Check access to the item.
            if not validate(object, object, None, o):
                raise Unauthorized, name
            object = o
            continue

        if name=='..':
            o = get(object, 'aq_parent', M)
            if o is not M:
                if not validate(object, object, name, o):
                    raise Unauthorized, name
                object=o
                continue

        t=get(object, '__bobo_traverse__', N)
        if name and name[:1] in '@+':
            # Process URI segment parameters.
            ns, nm = nsParse(name)
            if ns:
                try:
                    o = namespaceLookup(ns, nm, object, 
                                           REQUEST).__of__(object)
                    if not validate(object, object, name, o):
                        raise Unauthorized, name
                except TraversalError:
                    raise AttributeError(name)
        elif t is not N:
            o=t(REQUEST, name)

            container = None
            if aq_base(o) is not o:
                # The object is wrapped, so the acquisition
                # context determines the container.
                container = aq_parent(aq_inner(o))
            elif has(o, 'im_self'):
                container = o.im_self
            elif (has(aq_base(object), name) and get(object, name) == o):
                container = object
            if not validate(object, container, name, o):
                raise Unauthorized, name
        else:
            # Try an attribute.
            o = guarded_getattr(object, str(name), M) # failed on u'aq_parent'
            if o is M:
                # Try an item.
                try:
                    # XXX maybe in Python 2.2 we can just check whether
                    # the object has the attribute "__getitem__"
                    # instead of blindly catching exceptions.
                    try:
                        o = object[name]
                    except (AttributeError, KeyError):
                        # Try to look for a view
                        o = queryMultiAdapter((object, REQUEST), 
                                                 Interface, name)
                        if o is None:
                            # Didn't find one, reraise the error:
                            raise
                        o = o.__of__(object)
                except AttributeError, exc:
                    if str(exc).find('__getitem__') >= 0:
                        # The object does not support the item interface.
                        # Try to re-raise the original attribute error.
                        # XXX I think this only happens with
                        # ExtensionClass instances.
                        guarded_getattr(object, name)
                    raise
                except TypeError, exc:
                    if str(exc).find('unsubscriptable') >= 0:
                        # The object does not support the item interface.
                        # Try to re-raise the original attribute error.
                        # XXX This is sooooo ugly.
                        guarded_getattr(object, name)
                    raise
                else:
                    # Check access to the item.
                    if not validate(object, object, None, o):
                        raise Unauthorized, name
        object = o

    return object
