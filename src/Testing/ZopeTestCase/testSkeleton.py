##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Skeleton ZopeTestCase
"""

from Testing import ZopeTestCase


ZopeTestCase.installProduct('SomeProduct')


class TestSomeProduct(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        pass

    def testSomething(self):
        # Test something
        self.assertEqual(1 + 1, 2)


def test_suite():
    import unittest

    return unittest.defaultTestLoader.loadTestsFromTestCase(TestSomeProduct)
