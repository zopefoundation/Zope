##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Some menu code

$Id: menu.py 14512 2005-07-11 18:40:51Z philikon $
"""
from zope.interface import implements
from zope.app import zapi
from zope.app.publisher.interfaces.browser import IMenuAccessView
from zope.app.servicenames import BrowserMenu
from Products.Five import BrowserView

class MenuAccessView(BrowserView):
    implements(IMenuAccessView)

    def __getitem__(self, menu_id):
        browser_menu_service = zapi.getService(BrowserMenu)
        return browser_menu_service.getMenu(menu_id, self.context, self.request)
