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
import zope.app.pagetemplate

from Acquisition import aq_base
from Acquisition import aq_get
from Acquisition import aq_parent
from AccessControl import getSecurityManager
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.Expressions import createTrustedZopeEngine

_engine = createTrustedZopeEngine()
def getEngine():
    return _engine

class ViewPageTemplateFile(zope.app.pagetemplate.ViewPageTemplateFile):

    def pt_getEngine(self):
        return getEngine()

    def pt_getContext(self, instance, request, **kw):
        context = super(ViewPageTemplateFile, self).pt_getContext(
            instance, request, **kw)

        # get the root
        obj = context['context']
        root = None
        meth = aq_get(obj, 'getPhysicalRoot', None)
        if meth is not None:
            root = meth()

        context.update(here=context['context'],
                       # philiKON thinks container should be the view,
                       # but BBB is more important than aesthetics.
                       container=context['context'],
                       root=root,
                       modules=SecureModuleImporter,
                       traverse_subpath=[],  # BBB, never really worked
                       user = getSecurityManager().getUser()
                       )
        return context

# BBB
ZopeTwoPageTemplateFile = ViewPageTemplateFile
