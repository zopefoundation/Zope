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
from zope.interface import implements
from zope.tales.tales import Context, Iterator
from zope.tales.expressions import PathExpr, StringExpr, NotExpr
from zope.tales.expressions import DeferExpr, SubPathExpr, Undefs
from zope.tales.pythonexpr import PythonExpr
from zope.traversing.interfaces import ITraversable
from zope.traversing.adapters import traversePathElement
from zope.contentprovider.tales import TALESProviderExpression
from zope.proxy import removeAllProxies
import zope.app.pagetemplate.engine

import OFS.interfaces
from Acquisition import aq_base
from zExceptions import NotFound, Unauthorized
from Products.PageTemplates import ZRPythonExpr
from Products.PageTemplates.DeferExpr import LazyExpr
from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService

SecureModuleImporter = ZRPythonExpr._SecureModuleImporter()

# BBB 2005/05/01 -- remove after 12 months
import zope.deprecation
from zope.deprecation import deprecate
zope.deprecation.deprecated(
    ("StringExpr", "NotExpr", "PathExpr", "SubPathExpr", "Undefs"),
    "Zope 2 uses the Zope 3 ZPT engine now.  Expression types can be "
    "imported from zope.tales.expressions."
    )

# In Zope 2 traversal semantics, NotFound or Unauthorized (the Zope 2
# versions) indicate that traversal has failed.  By default, Zope 3's
# TALES engine doesn't recognize them as such which is why we extend
# Zope 3's list here and make sure our implementation of the TALES
# Path Expression uses them
ZopeUndefs = Undefs + (NotFound, Unauthorized)

def boboAwareZopeTraverse(object, path_items, econtext):
    """Traverses a sequence of names, first trying attributes then items.

    This uses Zope 3 path traversal where possible and interacts
    correctly with objects providing OFS.interface.ITraversable when
    necessary (bobo-awareness).
    """
    request = getattr(econtext, 'request', None)
    path_items = list(path_items)
    path_items.reverse()

    while path_items:
        name = path_items.pop()
        if OFS.interfaces.ITraversable.providedBy(object):
            object = object.restrictedTraverse(name)
        else:
            object = traversePathElement(object, name, path_items,
                                         request=request)
    return object

def render(ob, ns):
    """Calls the object, possibly a document template, or just returns
    it if not callable.  (From DT_Util.py)
    """
    if hasattr(ob, '__render_with_namespace__'):
        ob = ZRPythonExpr.call_with_ns(ob.__render_with_namespace__, ns)
    else:
        # items might be acquisition wrapped
        base = aq_base(ob)
        # item might be proxied (e.g. modules might have a deprecation
        # proxy)
        base = removeAllProxies(base)
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

class ZopePathExpr(PathExpr):

    def __init__(self, name, expr, engine):
        super(ZopePathExpr, self).__init__(name, expr, engine,
                                           boboAwareZopeTraverse)

    # override this to support different call metrics (see bottom of
    # method) and Zope 2's traversal exceptions (ZopeUndefs instead of
    # Undefs)
    def _eval(self, econtext):
        for expr in self._subexprs[:-1]:
            # Try all but the last subexpression, skipping undefined ones.
            try:
                ob = expr(econtext)
            except ZopeUndefs: # use Zope 2 expression types
                pass
            else:
                break
        else:
            # On the last subexpression allow exceptions through.
            ob = self._subexprs[-1](econtext)
            if self._hybrid:
                return ob

        if self._name == 'nocall':
            return ob

        # this is where we are different from our super class:
        return render(ob, econtext.vars)

    # override this to support Zope 2's traversal exceptions
    # (ZopeUndefs instead of Undefs)
    def _exists(self, econtext):
        for expr in self._subexprs:
            try:
                expr(econtext)
            except ZopeUndefs: # use Zope 2 expression types
                pass
            else:
                return 1
        return 0

class ZopeContext(Context):

    def translate(self, msgid, domain=None, mapping=None, default=None):
        context = self.contexts.get('context')
        return getGlobalTranslationService().translate(
            domain, msgid, mapping=mapping,
            context=context, default=default)

class ZopeEngine(zope.app.pagetemplate.engine.ZopeEngine):

    _create_context = ZopeContext

class ZopeIterator(Iterator):

    # The things below used to be attributes in
    # ZTUtils.Iterator.Iterator, however in zope.tales.tales.Iterator
    # they're methods.  We need BBB on the Python level so we redefine
    # them as properties here.  Eventually, we would like to get rid
    # of them, though, so that we won't have to maintain yet another
    # iterator class somewhere.

    @property
    def index(self):
        return super(ZopeIterator, self).index()

    @property
    def start(self):
        return super(ZopeIterator, self).start()

    @property
    def end(self):
        return super(ZopeIterator, self).end()

    @property
    def item(self):
        return super(ZopeIterator, self).item()

    # This method was on the old ZTUtils.Iterator.Iterator class but
    # isn't part of the spec.  We'll support it for a short
    # deprecation period.
    # BBB 2005/05/01 -- to be removed after 12 months
    @property
    @deprecate("The 'nextIndex' method has been deprecated and will disappear "
               "in Zope 2.12.  Use 'iterator.index+1' instead.")
    def nextIndex(self):
        return self.index + 1

    # 'first' and 'last' are Zope 2 enhancements to the TALES iterator
    # spec.  See help/tal-repeat.stx for more info
    def first(self, name=None):
        if self.start:
            return True
        return not self.same_part(name, self._last_item, self.item)

    def last(self, name=None):
        if self.end:
            return True
        return not self.same_part(name, self.item, self._next)

    def same_part(self, name, ob1, ob2):
        if name is None:
            return ob1 == ob2
        no = object()
        return getattr(ob1, name, no) == getattr(ob2, name, no) is not no

    # 'first' needs to have access to the last item in the loop
    def next(self):
        if self._nextIndex > 0:
            self._last_item = self.item
        return super(ZopeIterator, self).next()

class PathIterator(ZopeIterator):
    """A TALES Iterator with the ability to use first() and last() on
    subpaths of elements."""
    # we want to control our own traversal so that we can deal with
    # 'first' and 'last' when they appear in path expressions
    implements(ITraversable)

    def traverse(self, name, furtherPath):
        if name in ('first', 'last'):
            method = getattr(self, name)
            # it's important that 'name' becomes a copy because we'll
            # clear out 'furtherPath'
            name = furtherPath[:]
            if not name:
                name = None
            # make sure that traversal ends here with us
            furtherPath[:] = []
            return method(name)
        return getattr(self, name)

    def same_part(self, name, ob1, ob2):
        if name is None:
            return ob1 == ob2
        if isinstance(name, basestring):
            name = name.split('/')
        try:
            ob1 = boboAwareZopeTraverse(ob1, name, None)
            ob2 = boboAwareZopeTraverse(ob2, name, None)
        except ZopeUndefs:
            return False
        return ob1 == ob2

def createZopeEngine():
    e = ZopeEngine()
    e.iteratorFactory = PathIterator
    for pt in ZopePathExpr._default_type_names:
        e.registerType(pt, ZopePathExpr)
    e.registerType('string', StringExpr)
    e.registerType('python', ZRPythonExpr.PythonExpr)
    e.registerType('not', NotExpr)
    e.registerType('defer', DeferExpr)
    e.registerType('lazy', LazyExpr)
    e.registerType('provider', TALESProviderExpression)
    e.registerBaseName('modules', SecureModuleImporter)
    return e

def createTrustedZopeEngine():
    # same as createZopeEngine, but use non-restricted Python
    # expression evaluator
    e = createZopeEngine()
    e.types['python'] = PythonExpr
    return e

_engine = createZopeEngine()
def getEngine():
    return _engine
