##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
""" """

import os, sys, unittest, ZODB, Globals
from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.Folder import Folder


class ClassSecurityInfoTests(unittest.TestCase):


    def testSetPermissionDefault(self):
        """Test setting default roles for permissions."""

        # Setup a test class with default role -> permission decls.
        class Test(Folder):
            """Test class"""
            __ac_roles__ = ('Role A', 'Role B', 'Role C')

            meta_type = "Test"

            security = ClassSecurityInfo()

            security.setPermissionDefault(
                'Test permission',
                ('Manager', 'Role A', 'Role B', 'Role C')
                )

            security.declareProtected('Test permission', 'foo')
            def foo(self, REQUEST=None):
                """ """
                pass

        # Do class initialization.
        Globals.InitializeClass(Test)

        # Now check the resulting class to see if the mapping was made
        # correctly. Note that this uses carnal knowledge of the internal
        # structures used to store this information!
        object = Test()
        imPermissionRole = object.foo__roles__
        self.failUnless(len(imPermissionRole) == 4)
        for item in ('Manager', 'Role A', 'Role B', 'Role C'):
            self.failUnless(item in imPermissionRole)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ClassSecurityInfoTests))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
