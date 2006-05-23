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
from zope.tales.tales import ExpressionEngine, Context, Iterator
from zope.tales.expressions import PathExpr, StringExpr, NotExpr
from zope.tales.expressions import DeferExpr, SubPathExpr
from zope.tales.expressions import SimpleModuleImporter
from zope.tales.pythonexpr import PythonExpr
from zope.traversing.interfaces import ITraversable
from zope.traversing.adapters import traversePathElement
from zope.contentprovider.tales import TALESProviderExpression

import OFS.interfaces
from zExceptions import NotFound, Unauthorized
from Products.PageTemplates import ZRPythonExpr
from Products.PageTemplates.DeferExpr import LazyExpr
from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService

SecureModuleImporter = ZRPythonExpr._SecureModuleImporter()

# BBB 2005/05/01 -- remove after 12 months
import zope.deprecation
from zope.deprecation import deprecate
zope.deprecation.deprecated(
    ("StringExpr", "NotExpr", "PathExpr", "SubPathExpr"),
    "Zope 2 uses the Zope 3 ZPT engine now.  Expression types can be "
    "imported from zope.tales.expressions."
    )

def boboTraverseAwareSimpleTraverse(object, path_items, econtext):
    """A slightly modified version of zope.tales.expressions.simpleTraverse
    that interacts correctly with objects providing OFS.interfaces.ITraversable.
    """
    request = getattr(econtext, 'request', None)
    path_items = list(path_items)
    path_items.reverse()

    while path_items:
        name = path_items.pop()
        if OFS.interfaces.ITraversable.providedBy(object):
            try:
                object = object.restrictedTraverse(name)
            except (NotFound, Unauthorized), e:
                # OFS.Traversable.restrictedTraverse spits out
                # NotFound or Unauthorized (the Zope 2 versions) which
                # Zope 3's ZPT implementation obviously doesn't know
                # as exceptions indicating failed traversal.  Perhaps
                # the Zope 2's versions should be replaced with their
                # Zope 3 equivalent at some point.  For the time
                # being, however, we simply convert them into
                # LookupErrors:
                raise LookupError(*e.args)
        else:
            object = traversePathElement(object, name, path_items,
                                         request=request)
    return object

class ZopePathExpr(PathExpr):

    def __init__(self, name, expr, engine):
        super(ZopePathExpr, self).__init__(name, expr, engine,
                                           boboTraverseAwareSimpleTraverse)

class ZopeContext(Context):

    def translate(self, msgid, domain=None, mapping=None, default=None):
        context = self.contexts.get('context')
        return getGlobalTranslationService().translate(
            domain, msgid, mapping=mapping,
            context=context, default=default)

class ZopeEngine(ExpressionEngine):
    
    def getContext(self, contexts=None, **kwcontexts):
        if contexts is not None:
            if kwcontexts:
                kwcontexts.update(contexts)
            else:
                kwcontexts = contexts
        return ZopeContext(self, kwcontexts)

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
            ob1 = boboTraverseAwareSimpleTraverse(ob1, name, None)
            ob2 = boboTraverseAwareSimpleTraverse(ob2, name, None)
        except LookupError:
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
