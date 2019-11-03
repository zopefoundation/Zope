##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""Viewlet tests
"""

import unittest

from OFS.SimpleItem import SimpleItem
from Testing.ZopeTestCase import FunctionalDocFileSuite
from zope.interface import Interface
from zope.interface import implementer
from zope.viewlet import interfaces


@implementer(Interface)
class Content(SimpleItem):
    pass


class UnitTestSecurityPolicy:
    """
        Stub out the existing security policy for unit testing purposes.
    """
    # Standard SecurityPolicy interface
    def validate(self,
                 accessed=None,
                 container=None,
                 name=None,
                 value=None,
                 context=None,
                 roles=None,
                 *args, **kw):
        return 1

    def checkPermission(self, permission, object, context):
        return 1


class ILeftColumn(interfaces.IViewletManager):
    """Left column of my page."""


class INewColumn(interfaces.IViewletManager):
    """Left column of my page."""


class WeightBasedSorting:

    def sort(self, viewlets):
        def _key(info):
            return getattr(info[1], 'weight', 0)
        return sorted(viewlets, key=_key)


class Weather:
    weight = 0


class Stock:
    weight = 0

    def getStockTicker(self):
        return 'SRC $5.19'


class Sport:
    weight = 0

    def __call__(self):
        return 'Red Sox vs. White Sox'


class DynamicTempBox:
    weight = 0
    city = {'name': 'Los Angeles, CA', 'temp': 78}


def test_suite():
    return unittest.TestSuite([
        FunctionalDocFileSuite('README.txt'),
        FunctionalDocFileSuite('directives.txt'),
    ])
