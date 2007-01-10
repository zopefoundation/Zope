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

$Id$
"""
from zope.interface import implements
from zope.app.publisher.interfaces.browser import IMenuAccessView
from zope.app.publisher.browser.menu import getMenu
from Products.Five import BrowserView

class MenuAccessView(BrowserView):
    implements(IMenuAccessView)

    def __getitem__(self, menu_id):
        return getMenu(menu_id, self.context, self.request)
