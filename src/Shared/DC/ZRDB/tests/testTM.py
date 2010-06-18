##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from unittest import TestCase, TestSuite, makeSuite
from Shared.DC.ZRDB.TM import TM

class TestTM(TestCase):

    def test_sortKey(self):
        tm = TM()
        # the default Transaction Manager should have .sortKey() of 1 for
        # backward compatibility
        self.assertEquals(tm.sortKey(), 1)
        # but the sortKey() should be adjustable
        tm.setSortKey(())
        self.assertEquals(tm.sortKey(), ())

def test_suite():
    return TestSuite((makeSuite(TestTM),))
