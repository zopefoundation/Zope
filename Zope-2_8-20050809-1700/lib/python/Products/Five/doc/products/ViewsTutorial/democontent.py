##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from zope.interface import Interface, implements
from OFS.SimpleItem import SimpleItem
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

class IDemoContent(Interface):
    def mymethod():
        "Return some text"
        
class DemoContent(SimpleItem):
    implements(IDemoContent)

    meta_type = 'Five Demo Content'

    def __init__(self, id, title):
        self.id = id
        self.title = title

    def mymethod(self):
        return "Hello world"


manage_addDemoContentForm = PageTemplateFile(
    "www/demoContentAdd", globals(),
    __name__ = 'manage_addDemoContentForm')

def manage_addDemoContent(self, id, title, REQUEST=None):
    """Add the demo content."""
    id = self._setObject(id, DemoContent(id, title))
    if REQUEST is None:
        return
    REQUEST.RESPONSE.redirect(REQUEST['URL1'] + '/manage_main')
