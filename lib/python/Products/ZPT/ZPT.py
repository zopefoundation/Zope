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
"""Zope Page Template module

Zope object encapsulating a Page Template.
"""

__version__='$Revision: 1.48 $'[11:-2]

from types import StringType
from Globals import DTMLFile, ImageFile, MessageDialog, package_home, Persistent
from zLOG import LOG, ERROR, INFO
from OFS.SimpleItem import SimpleItem
from AccessControl import getSecurityManager

from zope.pagetemplate.pagetemplate import PageTemplate 
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

class ZPT(PageTemplate):
    "Zope wrapper for Page Template using TAL, TALES, and METAL"

    meta_type = 'ZPT'

    def __init__(self, id, text=None, content_type=None):
        self.id = str(id)

    pt_editForm = PageTemplateFile('www/ptEdit', globals(),
                                   __name__='pt_editForm')



def manage_addZPT(self, id, title=None, text=None,
                           REQUEST=None, submit=None):
    "Add a Page Template with optional file content."

    self._setObject(id, ZPT(id, text))
    ob = getattr(self, id)
    REQUEST.RESPONSE.redirect(self.absolute_url() + '/manage_main')
    

manage_addZPTForm = PageTemplateFile(
    'www/ptAdd', globals(), __name__='manage_addPageTemplateForm')

def initialize(context):
    context.registerClass(
        ZPT,
        permission='Add Page Templates',
        constructors=(manage_addZPTForm,
                      manage_addZPT),
        icon='www/zpt.gif',
        )
    context.registerHelp()
    context.registerHelpTitle('Zope Help')

