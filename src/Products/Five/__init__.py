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
"""Initialize the Five product
"""

# public API provided by Five
# usage: from Products.Five import <something>
from Products.Five.browser import BrowserView
from Products.Five.skin.standardmacros import StandardMacros

# some convenience methods/decorators

def fivemethod(func):
    func.__five_method__ = True
    return func

def isFiveMethod(m):
    return hasattr(m, '__five_method__')
