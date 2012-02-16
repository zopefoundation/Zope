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
"""Test browser pages
"""

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from OFS.SimpleItem import SimpleItem


class SimpleView(BrowserView):

    """More docstring. Please Zope"""

    def eagle(self):
        """Docstring"""
        return u"The eagle has landed"

    def eagle2(self):
        """Docstring"""
        return u"The eagle has landed:\n%s" % self.context.absolute_url()

    def mouse(self):
        """Docstring"""
        return u"The mouse has been eaten by the eagle"


class FancyView(BrowserView):

    """Fancy, fancy stuff"""

    def view(self):
        return u"Fancy, fancy"


class CallView(BrowserView):

    def __call__(self):
        return u"I was __call__()'ed"


class PermissionView(BrowserView, SimpleItem):

    def __call__(self):
        return u"I was __call__()'ed"


class CallTemplate(BrowserView):

    __call__ = ViewPageTemplateFile('falcon.pt')


class CallableNoDocstring:

    def __call__(self):
        return u"No docstring"


def function_no_docstring(self):
    return u"No docstring"


class NoDocstringView(BrowserView):

    def method(self):
        return u"No docstring"

    function = function_no_docstring

    object = CallableNoDocstring()


class NewStyleClass(object):

    """
    This is a testclass to verify that new style classes work
    in browser:page
    """

    def __init__(self, context, request):
        """Docstring"""
        self.context = context
        self.request = request

    def method(self):
        """Docstring"""
        return
