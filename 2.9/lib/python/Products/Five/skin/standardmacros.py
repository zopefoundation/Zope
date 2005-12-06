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

$Id: standardmacros.py 19283 2005-10-31 17:43:51Z philikon $
"""
import zope.interface

from zope.app import zapi
from Products.Five.browser import BrowserView

# this is a verbatim copy of zope.app.basicskin except that it doesn't
# derive from ``object``
class Macros:
    zope.interface.implements(zope.interface.common.mapping.IItemMapping)

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
            page = zapi.getMultiAdapter((context, request), name=name)
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
