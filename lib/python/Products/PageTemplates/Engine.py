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

from zope.tales.tales import ExpressionEngine
from zope.tales.expressions import PathExpr, StringExpr, NotExpr
from zope.tales.expressions import DeferExpr, SubPathExpr
from zope.tales.expressions import SimpleModuleImporter
from zope.tales.pythonexpr import PythonExpr
from zope.tales.tales import _valid_name, _parse_expr, NAME_RE, Undefined, Context 
from zope.i18n import translate
from zope.traversing.adapters import traversePathElement

from zExceptions import NotFound
from OFS.interfaces import ITraversable
from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService

_marker = object()

def boboTraverseAwareSimpleTraverse(object, path_items, econtext):
    """ a slightly modified version of zope.tales.expressions.simpleTraverse()
        that interacts correctly with objects implementing bobo_traverse().
    """
    request = getattr(econtext, 'request', None)
    path_items = list(path_items)
    path_items.reverse()

    while path_items:
        name = path_items.pop()
        if ITraversable.providedBy(object):
            try:
                object = object.restrictedTraverse(name)
            except NotFound, e:
                # OFS.Traversable.restrictedTraverse spits out
                # NotFound (the Zope 2 version) which Zope 3's ZPT
                # implementation obviously doesn't know as an
                # exception indicating failed traversal.  Perhaps Zope
                # 2's NotFound should be made to extend LookupError at
                # some point (or it should just be replaced with Zope
                # 3's version).  For the time being, however, we
                # simply converting NotFounds into LookupErrors:
                raise LookupError(*e.args)
        else:
            object = traversePathElement(object, name, path_items,
                                         request=request)
    return object


class ZopePathExpr(PathExpr):
    """Zope2-aware path expression implementation"""

    def __init__(self, name, expr, engine):
        super(ZopePathExpr, self).__init__(name, expr, engine,
                                           boboTraverseAwareSimpleTraverse)

class Context(Context):

    def translate(self, msgid, domain, mapping=None,
                  context=None, target_language=None, default=None):
        if context is None:
            context = self.contexts.get('context')
        return getGlobalTranslationService().translate(
            domain, msgid, mapping=mapping,
            context=context,
            default=default,
            target_language=target_language)


class ExpressionEngine(ExpressionEngine):
    
    def getContext(self, contexts=None, **kwcontexts):
        if contexts is not None:
            if kwcontexts:
                kwcontexts.update(contexts)
            else:
                kwcontexts = contexts
        return Context(self, kwcontexts)


def Engine():
    e = ExpressionEngine()
    for pt in ZopePathExpr._default_type_names:
        e.registerType(pt, ZopePathExpr)
    e.registerType('string', StringExpr)
    e.registerType('python', PythonExpr)
    e.registerType('not', NotExpr)
    e.registerType('defer', DeferExpr)
    e.registerBaseName('modules', SimpleModuleImporter())
    return e

Engine = Engine()
