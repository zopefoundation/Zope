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
"""Test fixtures
"""

from zope.interface import Interface, implements
from Products.Five import BrowserView

class IOne(Interface):
    """This is an interface.
    """

class One(object):
    'A class'
    implements(IOne)

class ViewOne(BrowserView):
    'Yet another class'

    def my_method(self, arg1, arg2, kw1=None, kw2='D'):
        print "CALLED %s %s %s %s" % (arg1, arg2, kw1, kw2)
