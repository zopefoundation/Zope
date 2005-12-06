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
"""Test browser pages

$Id: pages.py 12884 2005-05-30 13:10:41Z philikon $
"""
from Products.Five import BrowserView

class SimpleView(BrowserView):
    """More docstring. Please Zope"""

    def eagle(self):
        """Docstring"""
        return "The eagle has landed"

    def mouse(self):
        """Docstring"""
        return "The mouse has been eaten by the eagle"

class FancyView(BrowserView):
    """Fancy, fancy stuff"""

    def view(self):
        return "Fancy, fancy"

class CallView(BrowserView):

    def __call__(self):
        return "I was __call__()'ed"

class CallableNoDocstring:

    def __call__(self):
        return "No docstring"

def function_no_docstring(self):
    return "No docstring"

class NoDocstringView(BrowserView):

    def method(self):
        return "No docstring"

    function = function_no_docstring

    object = CallableNoDocstring()

class NewStyleClass(object):
    """
    This is a testclass to verify that new style classes are ignored
    in browser:page
    """

    def __init__(self, context, request):
        """Docstring"""
        self.context = context
        self.request = request

    def method(self):
        """Docstring"""
        return
