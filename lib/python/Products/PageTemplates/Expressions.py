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
from zope.tales.tales import ExpressionEngine, Context, Iterator
from zope.tales.expressions import PathExpr, StringExpr, NotExpr
from zope.tales.expressions import DeferExpr, SubPathExpr
from zope.tales.expressions import SimpleModuleImporter
from zope.tales.pythonexpr import PythonExpr
from zope.traversing.adapters import traversePathElement
from zope.contentprovider.tales import TALESProviderExpression

from zExceptions import NotFound, Unauthorized
from OFS.interfaces import ITraversable
from Products.PageTemplates import ZRPythonExpr
from Products.PageTemplates.DeferExpr import LazyExpr
from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService

SecureModuleImporter = ZRPythonExpr._SecureModuleImporter()

# BBB 2005/05/01 -- remove after 12 months
import zope.deprecation
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
        if ITraversable.providedBy(object):
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
            context=context,
            default=default)

class ZopeEngine(ExpressionEngine):
    
    def getContext(self, contexts=None, **kwcontexts):
        if contexts is not None:
            if kwcontexts:
                kwcontexts.update(contexts)
            else:
                kwcontexts = contexts
        return ZopeContext(self, kwcontexts)

class ZopeIterator(Iterator):

    __allow_access_to_unprotected_subobjects__ = True

    # these used to be properties in ZTUtils.Iterator.Iterator

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

    # these aren't in zope.tales.tales.Iterator, but were in
    # ZTUtils.Iterator.Iterator

    @property
    def nextIndex(self):
        return self.index + 1

    def first(self, name=None):
        if self.start:
            return True
        return not self.same_part(name, self._last, self.item)

    def last(self, name=None):
        if self.end:
            return True
        return not self.same_part(name, self.item, self._next)

    def same_part(self, name, ob1, ob2):
        if name is None:
            return ob1 == ob2
        no = object()
        return getattr(ob1, name, no) == getattr(ob2, name, no) is not no

def createZopeEngine():
    e = ZopeEngine()
    e.iteratorFactory = ZopeIterator
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
