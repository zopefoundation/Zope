##############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors.
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
"""Legacy browser view tests.

Here we nake sure that legacy implementations of views (e.g. those
which mix-in one of the Acquisition base classes without knowing
better) still work.
"""
import Acquisition
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class LegacyAttributes(BrowserView):
    """Make sure that those old aq_* attributes on Five BrowserViews
    still work, in particular aq_chain, even though BrowserView may
    not be an Acquisition-decendant class anymore...
    """

    def __call__(self):
        return repr([obj for obj in self.aq_chain])

class LegacyTemplate(BrowserView):

    template = ViewPageTemplateFile('falcon.pt')

    def __call__(self):
        return self.template()

class Explicit(Acquisition.Explicit):

    def render(self):
        return 'Explicit'

class ExplicitWithTemplate(Acquisition.Explicit):

    template = ViewPageTemplateFile('falcon.pt')

class Implicit(Acquisition.Implicit):

    def render(self):
        return 'Implicit'

class ImplicitWithTemplate(Acquisition.Implicit):

    template = ViewPageTemplateFile('falcon.pt')
