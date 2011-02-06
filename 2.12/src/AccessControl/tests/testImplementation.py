##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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

## Note - this test is disabled because the intent for 2.7 was *not*
## to support the ability to arbitrarily switch the security policy
## at any time (which would currently be nearly impossible to do in
## a way that would be sane for 3rd party apps that may already have
## imported parts of the security machinery), but just to make sure
## that the config file could be used to initially set the implementation
## to be used. The policy setting is 'initialize once' - setImplementation
## should not be called either by user code or unit tests, as the
## effects are officially undefined.
        
##     def test_setImplemenationC(self):
##         setImplementation("C")
##         name = getImplementationName()
##         if self.have_cAccessControl:
##             self.assertEqual(name, "C")
##         else:
##             self.assertEqual(name, "PYTHON")

##     def test_setImplemenationPython(self):
##         setImplementation("Python")
##         self.assertEqual(getImplementationName(), "PYTHON")


def test_suite():
    return unittest.makeSuite(AccessControlImplementationTest)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
