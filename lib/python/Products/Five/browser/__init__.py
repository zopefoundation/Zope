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
import Acquisition
import zope.publisher.browser

class BrowserView(zope.publisher.browser.BrowserView):

    # BBB for code that expects BrowserView to still inherit from
    # Acquisition.Explicit.

    def __of__(self, context):
        # Technically this isn't in line with the way Acquisition's
        # __of__ works.  With Acquisition, you get a wrapper around
        # the original object and only that wrapper's parent is the
        # new context.  Here we change the original object.
        #self.__parent__ = context  # ugh. segfault!

        return self

    # XXX Classes which are still based on Acquisition and access
    # self.context in a method need to call aq_inner on it, or get a funky
    # aq_chain. We do this here for BBB friendly purposes.

    def __getParent(self):
        return getattr(self, '_parent', Acquisition.aq_inner(self.context))

    def __setParent(self, parent):
        self._parent = parent

    aq_parent = __parent__ = property(__getParent, __setParent)

    # We provide the aq_* properties here for BBB

    aq_self = aq_inner = aq_base = property(lambda self: self)

    @property
    def aq_chain(self):
        return Acquisition.aq_chain(self)
