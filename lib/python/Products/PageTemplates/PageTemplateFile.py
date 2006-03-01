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

import os

from Globals import package_home, InitializeClass
from App.config import getConfiguration
from ZopePageTemplate import ZopePageTemplate
from zope.app.content_types import guess_content_type
import AccessControl

from ComputedAttribute import ComputedAttribute
from OFS.SimpleItem import SimpleItem
from Expressions import SecureModuleImporter
from OFS.Traversable import Traversable
from zope.pagetemplate.pagetemplatefile import PageTemplateFile as PTF
from zope.pagetemplate.pagetemplate import PageTemplate as PT

from Shared.DC.Scripts.Script import Script

from OFS.SimpleItem import Item_w__name__
from Shared.DC.Scripts.Signature import FuncCode


from zope.tales.tales import ExpressionEngine
from zope.tales.expressions import PathExpr, StringExpr, NotExpr, DeferExpr, SubPathExpr
from zope.tales.tales import _valid_name, _parse_expr, NAME_RE, Undefined 
from zope.tales.expressions import SimpleModuleImporter
from zope.tales.pythonexpr import PythonExpr

from zope.tales.expressions import PathExpr

_marker = object()

def extendedSimpleTraverse(object, path_items, econtext):
    """Traverses a sequence of names, first trying attributes then items.
    """

    for name in path_items:
        next = getattr(object, name, _marker)
        if next is not _marker:
            object = next
        elif hasattr(object, '__getitem__'):
            try:
                object = object[name]
            except:
                # FIX bare try..except
                object = object.restrictedTraverse(name)
        else:
            # Allow AttributeError to propagate
            object = getattr(object, name)
    return object



class MyPathExpr(PathExpr):

    def __init__(self, name, expr, engine, traverser=extendedSimpleTraverse):
        self._s = expr
        self._name = name
        paths = expr.split('|')
        self._subexprs = []
        add = self._subexprs.append
        for i in range(len(paths)):
            path = paths[i].lstrip()
            if _parse_expr(path):
                # This part is the start of another expression type,
                # so glue it back together and compile it.
                add(engine.compile('|'.join(paths[i:]).lstrip()))
                break
            add(SubPathExpr(path, traverser, engine)._eval)



def Engine():
    e = ExpressionEngine()
    reg = e.registerType
    for pt in MyPathExpr._default_type_names:
        reg(pt, MyPathExpr)
    reg('string', StringExpr)
    reg('python', PythonExpr)
    reg('not', NotExpr)
    reg('defer', DeferExpr)
    e.registerBaseName('modules', SimpleModuleImporter())
    return e

Engine = Engine()



class PageTemplateFile(SimpleItem, Script, PT, Traversable):


    func_defaults = None
    func_code = FuncCode((), 0)
    _v_last_read = 0

    # needed by App.class_init.default__class_init__, often imported
    # using the alias Globals.InitializeClass
    _need__name__ = 1

    _default_bindings = {'name_subpath': 'traverse_subpath'}

    security = AccessControl.ClassSecurityInfo()
    security.declareProtected('View management screens',
      'read', 'document_src')

    _default_bindings = {'name_subpath': 'traverse_subpath'}


    def __init__(self, filename, _prefix=None, **kw):

        name = None
        if kw.has_key('__name__'):
            name = kw['__name__']
            del kw['__name__'] 

        basepath, ext = os.path.splitext(filename)

        if name:
            self.id = self.__name__ = name
        else:
            self.id = self.__name__ = os.path.basename(basepath)

        if _prefix:
            if isinstance(_prefix, str):
                filename = os.path.join(_prefix, filename)
            else:
                filename = os.path.join(package_home(_prefix), filename)

        if not ext:
            filename = filename + '.zpt'

        self.filename = filename

        content = open(filename).read()

        from ZopePageTemplate import guess_type
        self.pt_edit( content, guess_type(filename, content))


    def pt_getContext(self):
        root = self.getPhysicalRoot()
        context = self._getContext()
        from DateTime.DateTime import DateTime
        c = {'template': self,
             'here': context,
             'context': context,
             'container': self._getContainer(),
             'nothing': None,
             'options': {},
             'root': root,
             'DateTime' : DateTime,
             'request': getattr(root, 'REQUEST', None),
             'modules': SecureModuleImporter,
             }
        return c

    def _exec(self, bound_names, args, kw):
        """Call a Page Template"""
        self._cook_check()
        if not kw.has_key('args'):
            kw['args'] = args
        bound_names['options'] = kw

        try:
            response = self.REQUEST.RESPONSE
            if not response.headers.has_key('content-type'):
                response.setHeader('content-type', self.content_type)
        except AttributeError:
            pass

        # Execute the template in a new security context.
        security = AccessControl.getSecurityManager()
        bound_names['user'] = security.getUser()
        security.addContext(self)

        try:
            context = self.pt_getContext()
            context.update(bound_names)
            return self.pt_render(context)
        finally:
            security.removeContext(self)

    def pt_macros(self):
        self._cook_check()
        return PageTemplate.pt_macros(self)

    def document_src(self, REQUEST=None, RESPONSE=None):
        """Return expanded document source."""

        if RESPONSE is not None:
            # Since _cook_check() can cause self.content_type to change,
            # we have to make sure we call it before setting the
            # Content-Type header.
            self._cook_check()
            RESPONSE.setHeader('Content-Type', 'text/plain')
        return self.read()

    def _get__roles__(self):
        imp = getattr(aq_parent(aq_inner(self)),
                      '%s__roles__' % self.__name__)
        if hasattr(imp, '__of__'):
            return imp.__of__(self)
        return imp

    __roles__ = ComputedAttribute(_get__roles__, 1)

    def getOwner(self, info=0):
        """Gets the owner of the executable object.

        This method is required of all objects that go into
        the security context stack.  Since this object came from the
        filesystem, it is owned by no one managed by Zope.
        """
        return None

    def pt_getEngine(self):
        return Engine

    def __getstate__(self):
        from ZODB.POSException import StorageError
        raise StorageError, ("Instance of AntiPersistent class %s "
                             "cannot be stored." % self.__class__.__name__)

InitializeClass(PageTemplateFile)
