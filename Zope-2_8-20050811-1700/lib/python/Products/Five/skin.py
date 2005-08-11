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
"""Mimick the Zope 3 skinning system in Five.

$Id: skin.py 12915 2005-05-31 10:23:19Z philikon $
"""
from zope.interface.common.mapping import IItemMapping
from zope.interface import implements
from zope.component import getView
from Products.Five.browser import BrowserView

# this is a verbatim copy of zope.app.basicskin except that it doesn't
# derive from ``object``
class Macros:
    implements(IItemMapping)

    macro_pages = ()
    aliases = {
        'view': 'page',
        'dialog': 'page',
        'addingdialog': 'page'
        }

    def __getitem__(self, key):
        key = self.aliases.get(key, key)
        context = self.context
        request = self.request
        for name in self.macro_pages:
            page = getView(context, name, request)
            try:
                v = page[key]
            except KeyError:
                pass
            else:
                return v
        raise KeyError, key


class StandardMacros(BrowserView, Macros):
    macro_pages = ('five_template',
                   'widget_macros',
                   'form_macros',) 

# copy of zope.app.form.browser.macros.FormMacros
class FormMacros(StandardMacros):    
    macro_pages = ('widget_macros', 'addform_macros')
