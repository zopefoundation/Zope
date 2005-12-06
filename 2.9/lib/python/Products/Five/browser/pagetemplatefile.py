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

$Id: pagetemplatefile.py 15193 2005-07-27 13:27:04Z regebro $
"""
import os, sys

from Globals import package_home
from AccessControl import getSecurityManager
from Shared.DC.Scripts.Bindings import Unauthorized, UnauthorizedBinding
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from zope.app.pagetemplate.viewpagetemplatefile import ViewMapper
from zope.app.pagetemplate.viewpagetemplatefile import ViewPageTemplateFile

from Products.Five.browser.ReuseUtils import rebindFunction
from Products.Five.browser.TrustedExpression import getEngine, ModuleImporter

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
        try:
            root = self.getPhysicalRoot()
            view = self._getContext()
        except AttributeError:
            # self has no attribute getPhysicalRoot. This typically happens 
            # when the template has no proper acquisition context. 
            # That also means it has no view.  /regebro
            root = self.context.getPhysicalRoot()
            view = None

        here = self.context.aq_inner

        request = getattr(root, 'REQUEST', None)
        c = {'template': self,
             'here': here,
             'context': here,
             'container': here,
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
