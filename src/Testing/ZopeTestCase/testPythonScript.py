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
"""Example ZopeTestCase testing a PythonScript in the default fixture

This test module demonstrates the security API of ZopeTestCase.

Note that you are encouraged to call any of the following methods to
modify the test user's security credentials:

    setRoles()
    setPermissions()
    login()
    logout()

$Id$
"""

from Testing import ZopeTestCase

ZopeTestCase.installProduct('PythonScripts')

from AccessControl import Unauthorized
from AccessControl import getSecurityManager

access_permissions = ['View management screens']
change_permissions = ['Change Python Scripts']

ps_params1 = 'a=1'
ps_body1 = 'return a'
ps_params2 = 'a'
ps_body2 = 'return a+1'


class TestPythonScript(ZopeTestCase.ZopeTestCase):
    '''Tries various things allowed by the ZopeTestCase API.'''

    def afterSetUp(self):
        '''Adds a PythonScript object to the default fixture'''
        dispatcher = self.folder.manage_addProduct['PythonScripts']
        dispatcher.manage_addPythonScript('ps')
        self.ps = self.folder['ps']
        self.ps.ZPythonScript_edit(ps_params1, ps_body1)

    # Test the setup

    def testSetup(self):
        # The PythonScript should exist and be properly set up
        self.failUnless(hasattr(self.folder, 'ps'))
        self.assertEqual(self.ps.body(), ps_body1+'\n')
        self.assertEqual(self.ps.params(), ps_params1)
        owner = self.ps.getOwner()
        self.assertEqual(owner.getUserName(), ZopeTestCase.user_name)

    # Test the script(s)

    def testCanCallScript1WithArgument(self):
        # PythonScript should return 2
        self.assertEqual(self.ps(2), 2)

    def testCanCallScript1WithoutArgument(self):
        # PythonScript should return 1
        self.assertEqual(self.ps(), 1)

    def testCanCallScript2WithArgument(self):
        # PythonScript should return 2
        self.ps.ZPythonScript_edit(ps_params2, ps_body2)
        self.assertEqual(self.ps(1), 2)

    def testCannotCallScript2WithoutArgument(self):
        # PythonScript should raise a TypeError if called without arguments
        self.ps.ZPythonScript_edit(ps_params2, ps_body2)
        self.assertRaises(TypeError, self.ps, ())

    # Test access protection with restrictedTraverse

    def testCannotAccessWithoutAccessPermission(self):
        # manage_main should be protected
        self.assertRaises(Unauthorized, self.ps.restrictedTraverse, 'manage_main')

    def testCanAccessWithAccessPermission(self):
        # manage_main should be accessible if we have the necessary permissions
        self.setPermissions(access_permissions)
        try:
            self.ps.restrictedTraverse('manage_main')
        except Unauthorized:
            self.fail('Access to manage_main was denied')

    def testCannotAccessIfAnonymous(self):
        # manage_main should be protected from Anonymous
        self.logout()
        self.assertRaises(Unauthorized, self.ps.restrictedTraverse, 'manage_main')

    def testCanAccessIfManager(self):
        # manage_main should be accessible to Manager
        self.setRoles(['Manager'])
        try:
            self.ps.restrictedTraverse('manage_main')
        except Unauthorized:
            self.fail('Access to manage_main was denied to Manager')

    # Test access protection with SecurityManager

    def testCannotAccessWithoutAccessPermissionSecurityManager(self):
        # manage_main should be protected
        self.assertRaises(Unauthorized, getSecurityManager().validate,
                          self.ps, self.ps, 'manage_main', self.ps.manage_main)

    def testCanAccessWithAccessPermissionSecurityManager(self):
        # manage_main should be accessible if we have the necessary permissions
        self.setPermissions(access_permissions)
        try:
            getSecurityManager().validate(self.ps, self.ps, 'manage_main', self.ps.manage_main)
        except Unauthorized:
            self.fail('Access to manage_main was denied')

    def testCannotAccessIfAnonymousSecurityManager(self):
        # manage_main should be protected from Anonymous
        self.logout()
        self.assertRaises(Unauthorized, getSecurityManager().validate,
                          self.ps, self.ps, 'manage_main', self.ps.manage_main)

    def testCanAccessIfManagerSecurityManager(self):
        # manage_main should be accessible to Manager
        self.setRoles(['Manager'])
        try:
            getSecurityManager().validate(self.ps, self.ps, 'manage_main', self.ps.manage_main)
        except Unauthorized:
            self.fail('Access to manage_main was denied to Manager')

    # Test edit protection with restrictedTraverse

    def testCannotEditWithoutChangePermission(self):
        # PythonScript should not be editable
        try:
            self.ps.restrictedTraverse('ZPythonScript_edit')(ps_params2, ps_body2)
        except Unauthorized:
            pass    # Test passed
        else:
            self.assertEqual(self.ps.body(), ps_body2+'\n', 
                    'ZPythonScript_edit was not protected')
            self.assertEqual(self.ps.body(), ps_body1+'\n', 
                    'ZPythonScript_edit was protected but no exception was raised')

    def testCanEditWithChangePermission(self):
        # PythonScript should be editable if we have the necessary permissions
        self.setPermissions(change_permissions)
        try:
            self.ps.restrictedTraverse('ZPythonScript_edit')(ps_params2, ps_body2)
        except Unauthorized:
            self.fail('Access to ZPythonScript_edit was denied')
        else:
            self.assertEqual(self.ps.body(), ps_body2+'\n')
            self.assertEqual(self.ps.params(), ps_params2)

    def testCannotEditIfAnonymous(self):
        # PythonScript should not be editable by Anonymous
        self.logout()
        try:
            self.ps.restrictedTraverse('ZPythonScript_edit')(ps_params2, ps_body2)
        except Unauthorized:
            pass    # Test passed
        else:
            self.assertEqual(self.ps.body(), ps_body2+'\n', 
                    'ZPythonScript_edit was not protected')
            self.assertEqual(self.ps.body(), ps_body1+'\n', 
                    'ZPythonScript_edit was protected but no exception was raised')

    def testCanEditIfManager(self):
        # PythonScript should be editable by Manager
        self.setRoles(['Manager'])
        try:
            self.ps.restrictedTraverse('ZPythonScript_edit')(ps_params2, ps_body2)
        except Unauthorized:
            self.fail('Access to ZPythonScript_edit was denied to Manager')
        else:
            self.assertEqual(self.ps.body(), ps_body2+'\n')
            self.assertEqual(self.ps.params(), ps_params2)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPythonScript))
    return suite

