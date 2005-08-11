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

$Id: pagetemplatefile.py 12915 2005-05-31 10:23:19Z philikon $
"""
import os, sys

# Zope 2
from Globals import package_home
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

# Zope 3
from zope.app.pagetemplate.viewpagetemplatefile import ViewMapper
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

# Five
from ReuseUtils import rebindFunction
from TrustedExpression import getEngine, ModuleImporter

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
 
    def get_path_from_prefix(self, _prefix):
        if isinstance(_prefix, str):
            path = _prefix
        else:
            if _prefix is None:
                _prefix = sys._getframe(2).f_globals
            path = package_home(_prefix)
        return path 

    _cook = rebindFunction(PageTemplateFile._cook,
                           getEngine=getEngine)
    
    pt_render = rebindFunction(PageTemplateFile.pt_render,
                               getEngine=getEngine)

    def _pt_getContext(self):
        view = self._getContext()
        try:
            root = self.getPhysicalRoot()
            here = view.context
        except AttributeError:
            # self has no attribute getPhysicalRoot.
            # This typically happens when the template has
            # no proper acquisition context. That means it has no view,
            # since that's the normal context for a template in Five. /regebro
            root = self.context.getPhysicalRoot()
            here = self.context
            view = None

        request = getattr(root, 'REQUEST', None)
        c = {'template': self,
             'here': here,
             'context': here,
             'container': self._getContainer(),
             'nothing': None,
             'options': {},
             'root': root,
             'request': request,
             'modules': ModuleImporter,
             }
        if view:
            c['view'] = view
            c['views'] = ViewMapper(here, request)

        return c

    pt_getContext = rebindFunction(_pt_getContext,
                                   SecureModuleImporter=ModuleImporter)

# this is not in use right now, but would be how to integrate Zope 3 page
# templates instead of Zope 2 page templates
class FivePageTemplateFile(ViewPageTemplateFile):
    
    def pt_getContext(self, instance, request, **_kw):
        # instance is a View component
        namespace = super(FivePageTemplateFile, self).pt_getContext(
            instance, request, **_kw)
        namespace['here'] = namespace['context']
        return namespace
