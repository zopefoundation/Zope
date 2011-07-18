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
"""Provide basic browser functionality
"""

import Acquisition
import zope.publisher.browser

from Products.Five.bbb import AcquisitionBBB


class BrowserView(zope.publisher.browser.BrowserView, AcquisitionBBB):

    # Use an explicit __init__ to work around problems with magically inserted
    # super classes when using BrowserView as a base for viewlets.
    def __init__(self, context, request):
        self.context = context
        self.request = request

    # Classes which are still based on Acquisition and access
    # self.context in a method need to call aq_inner on it, or get a
    # funky aq_chain. We do this here for BBB friendly purposes.

    def __getParent(self):
        return getattr(self, '_parent', Acquisition.aq_inner(self.context))

    def __setParent(self, parent):
        self._parent = parent

    aq_parent = __parent__ = property(__getParent, __setParent)
