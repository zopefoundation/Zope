##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Test that the Zope schema can be loaded."""

import unittest

import Zope.Startup


class StartupTestCase(unittest.TestCase):

    def test_load_schema(self):
        Zope.Startup.getSchema()


def test_suite():
    return unittest.makeSuite(StartupTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
