##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""A 'PageTemplateFile' without security restrictions.

$Id$
"""
import os, sys

from Acquisition import aq_inner
from Globals import package_home
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.Expressions import createTrustedZopeEngine
from zope.app.pagetemplate.viewpagetemplatefile import ViewMapper

_engine = createTrustedZopeEngine()
def getEngine():
    return _engine

class ZopeTwoPageTemplateFile(PageTemplateFile):
    """A strange hybrid between Zope 2 and Zope 3 page template.

    Uses Zope 2's engine, but with security disabled and with some
    initialization and API from Zope 3.
    """

    def __init__(self, filename, _prefix=None, content_type=None):
        # XXX doesn't use content_type yet

        self.ZBindings_edit(self._default_bindings)

        path = self.get_path_from_prefix(_prefix)
        self.filename = os.path.join(path, filename)
        if not os.path.isfile(self.filename):
            raise ValueError("No such file", self.filename)

        basepath, ext = os.path.splitext(self.filename)
        self.__name__ = os.path.basename(basepath)

        super(PageTemplateFile, self).__init__(self.filename, _prefix)

    def get_path_from_prefix(self, _prefix):
        if isinstance(_prefix, str):
            path = _prefix
        else:
            if _prefix is None:
                _prefix = sys._getframe(2).f_globals
            path = package_home(_prefix)
        return path

    def pt_getEngine(self):
        return getEngine()

    def pt_getContext(self):
        try:
            root = self.getPhysicalRoot()
        except AttributeError:
            try:
                root = self.context.getPhysicalRoot()
            except AttributeError:
                root = None

        # Even if the context isn't a view (when would that be exaclty?),
        # there shouldn't be any dange in applying a view, because it
        # won't be used.  However assuming that a lack of getPhysicalRoot
        # implies a missing view causes problems.
        view = self._getContext()

        here = aq_inner(self.context)

        request = getattr(root, 'REQUEST', None)
        c = {'template': self,
             'here': here,
             'context': here,
             'container': here,
             'nothing': None,
             'options': {},
             'root': root,
             'request': request,
             'modules': SecureModuleImporter,
             }
        if view is not None:
            c['view'] = view
            c['views'] = ViewMapper(here, request)

        return c

ViewPageTemplateFile = ZopeTwoPageTemplateFile
