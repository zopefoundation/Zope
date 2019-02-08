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
"""Example doctest
"""

from Testing.ZopeTestCase import ZopeDocFileSuite
from unittest import TestSuite


def test_suite():
    return TestSuite((
        ZopeDocFileSuite('WarningsTest.txt'),
    ))
