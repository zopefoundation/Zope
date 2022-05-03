##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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
"""Mimick the zope.app.basicskin skinning system.
"""

import zope.component
import zope.interface
from Products.Five.browser import BrowserView


@zope.interface.implementer(zope.interface.common.mapping.IItemMapping)
class Macros:

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
            page = zope.component.getMultiAdapter(
                (context, request), name=name)
            try:
                v = page[key]
            except KeyError:
                pass
            else:
                return v
        raise KeyError(key)


class StandardMacros(BrowserView, Macros):
    macro_pages = (
        'five_template',
        'widget_macros',
        'form_macros',
    )
