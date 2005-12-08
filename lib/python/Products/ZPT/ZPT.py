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
import AccessControl
from AccessControl import getSecurityManager

from zope.pagetemplate.pagetemplate import PageTemplate 
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

class ZPT(SimpleItem, PageTemplate):
    "Zope wrapper for Page Template using TAL, TALES, and METAL"

    meta_type = 'ZPT'

    manage_options = (
        {'label':'Edit', 'action':'pt_editForm',
         'help': ('PageTemplates', 'PageTemplate_Edit.stx')},
        {'label':'Test', 'action':'ZScriptHTML_tryForm'},
        ) \
        + SimpleItem.manage_options \
        
    security = AccessControl.ClassSecurityInfo()

    def __init__(self, id, text=None, content_type=None):
        self.id = str(id)

    security.declareProtected('View', '__call__')
    security.declareProtected('View', 'view')
    def view(self):
        """view """
        return self()

    security.declareProtected('Change Page Templates',
      'pt_editAction', 'pt_setTitle', 'pt_edit',
      'pt_upload', 'pt_changePrefs')
    def pt_editAction(self, REQUEST, title, text, content_type, expand):
        """Change the title and document."""

        print text
        print content_type
        self.pt_edit(text, content_type)
        message= 'done'
        return self.pt_editForm(manage_tabs_message=message)


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

