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
"""Provide basic browser functionality

$Id$
"""

import zope.publisher.browser

from Acquisition import aq_chain
from Acquisition import aq_inner

class BrowserView(zope.publisher.browser.BrowserView):

    # BBB for code that expects BrowserView to still inherit from
    # Acquisition.Explicit.

    def __of__(self, context):
        return self

    # XXX Classes which are still based on Acquisition and access
    # self.context in a method need to call aq_inner on it, or get a funky
    # aq_chain. We do this here for BBB friendly purposes.

    def __getParent(self):
        return getattr(self, '_parent', aq_inner(self.context))

    def __setParent(self, parent):
        self._parent = parent

    __parent__ = property(__getParent, __setParent)

    # We provide the aq_* properties here for BBB

    @property
    def aq_base(self):
        return self

    aq_self = aq_inner = aq_base

    @property
    def aq_parent(self):
        return self.__parent__

    @property
    def aq_chain(self):
        return aq_chain(self)
