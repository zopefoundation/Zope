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

from Products.Five import BrowserView
from zope.interface import Interface
from zope.interface import implementer


class IOne(Interface):
    """This is an interface.
    """


@implementer(IOne)
class One:
    'A class'


class ViewOne(BrowserView):
    'Yet another class'

    def my_method(self, arg1, arg2, kw1=None, kw2='D'):
        print(f'CALLED {arg1} {arg2} {kw1} {kw2}')
