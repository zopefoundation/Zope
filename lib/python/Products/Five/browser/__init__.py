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

    # counter = 0

    def __of__(self, context):
        # Technically this isn't in line with the way Acquisition's
        # __of__ works.  With Acquisition, you get a wrapper around
        # the original object and only that wrapper's parent is the
        # new context.  Here we change the original object.
        
        # XXX The first segfault happens in form.tests.forms.txt in the first
        # line of the "Widget Overrides" chapter (line 154).

        # What causes it is:
        
        # ../zope2/lib/python/Zope2/App/startup.py(199)__call__()
        # -> log = aq_acquire(published, '__error_log__', containment=1)
        
        # Which causes an infinite loop :(
        
        # self.__parent__ = context  # ugh. segfault!
        # self.counter = self.counter + 1
        # if self.counter > 10:
        #     import pdb; pdb.set_trace()

        return self

    # Classes which are still based on Acquisition and access
    # self.context in a method need to call aq_inner on it, or get a
    # funky aq_chain. We do this here for BBB friendly purposes.

    def __getParent(self):
        return getattr(self, '_parent', Acquisition.aq_inner(self.context))

    def __setParent(self, parent):
        self._parent = parent

    aq_parent = __parent__ = property(__getParent, __setParent)

    # We provide the aq_* properties here for BBB
    aq_self = aq_inner = aq_base = property(lambda self: self)
    aq_chain = property(Acquisition.aq_chain)

    def aq_acquire(self, *args, **kw):
        return Acquisition.aq_acquire(self, *args, **kw)

    def aq_inContextOf(self, *args, **kw):
        return Acquisition.aq_inContextOf(self, *args, **kw)

