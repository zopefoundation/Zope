##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test layer extraction feature
"""

from unittest import TestSuite
from Testing import ZopeTestCase
from Testing.ZopeTestCase import ZopeDocFileSuite
from Testing.ZopeTestCase import ZopeDocTestSuite
from Testing.ZopeTestCase import transaction
from Testing.ZopeTestCase import layer


class TestLayer(layer.ZopeLite):
    """
    If the layer is extracted properly, we should see the following
    variable

    >>> getattr(self.app, 'LAYER_EXTRACTED', False)
    True
    """

    @classmethod
    def setUp(cls):
        app = ZopeTestCase.app()
        app.LAYER_EXTRACTED = True
        transaction.commit()
        ZopeTestCase.close(app)

    @classmethod
    def tearDown(cls):
        app = ZopeTestCase.app()
        delattr(app, 'LAYER_EXTRACTED')
        transaction.commit()
        ZopeTestCase.close(app)


class TestCase(ZopeTestCase.ZopeTestCase):
    layer = TestLayer


def test_suite():
    return TestSuite((
        ZopeDocTestSuite(test_class=TestCase),
        ZopeDocFileSuite('layerextraction.txt', test_class=TestCase),
    ))

