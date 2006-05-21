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
"""Page Template module

$Id$
"""
import ExtensionClass
import zope.pagetemplate.pagetemplate
from zope.tales.expressions import SimpleModuleImporter
from Products.PageTemplates.Expressions import getEngine
from Products.PageTemplates.Expressions import SecureModuleImporter

##############################################################################
# BBB 2005/05/01 -- to be removed after 12 months
_ModuleImporter = SimpleModuleImporter
ModuleImporter = SimpleModuleImporter()
import zope.deprecation
zope.deprecation.deprecated(
    ('ModuleImporter', '_ModuleImporter'),
    "Zope 2 uses the Zope 3 ZPT engine now.  ModuleImporter has moved "
    "to zope.pagetemplate.pagetemplate.SimpleModuleImporter (this is a "
    "class, not an instance)."
    )

import zope.deferredimport
zope.deferredimport.deprecatedFrom(
    "It has moved to zope.pagetemplate.pagetemplate.  This reference will "
    "be gone in Zope 2.12.",
    'zope.pagetemplate.pagetemplate',
    'PTRuntimeError', 'PageTemplateTracebackSupplement'
    )
##############################################################################

class PageTemplate(ExtensionClass.Base,
                   zope.pagetemplate.pagetemplate.PageTemplate):

    def pt_getEngine(self):
        return getEngine()

    def pt_getContext(self, args=(), options={}):
        c = super(PageTemplate, self).pt_getContext(args, options)
        c.update({
            'request': None,
            'modules': SimpleModuleImporter(),
            })
        parent = getattr(self, 'aq_parent', None)
        if parent is not None:
            c['here'] = parent
            c['context'] = parent
            c['container'] = self.aq_inner.aq_parent
            while parent is not None:
                self = parent
                parent = getattr(self, 'aq_parent', None)
            c['root'] = self
        return c
