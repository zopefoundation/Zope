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
"""Test of the implementation selection support."""

import unittest

from AccessControl.Implementation import getImplementationName
from AccessControl.Implementation import setImplementation


class AccessControlImplementationTest(unittest.TestCase):

    have_cAccessControl = None

    def setUp(self):
        if self.have_cAccessControl is None:
            try:
                import AccessControl.cAccessControl
            except ImportError:
                v = False
            else:
                v = True
            self.__class__.have_cAccessControl = v
        self.original = getImplementationName()

    def tearDown(self):
        setImplementation(self.original)

    def test_setImplemenationC(self):

        # XXX:  'C' ZSP is not yet working
        self.assertRaises( NotImplementedError, setImplementation, "C")
        return

        setImplementation("C")
        name = getImplementationName()
        if self.have_cAccessControl:
            self.assertEqual(name, "C")
        else:
            self.assertEqual(name, "PYTHON")

    def test_setImplemenationPython(self):
        setImplementation("Python")
        self.assertEqual(getImplementationName(), "PYTHON")


def test_suite():
    return unittest.makeSuite(AccessControlImplementationTest)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
