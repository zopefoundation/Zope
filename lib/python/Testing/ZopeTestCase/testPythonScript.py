##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Example ZopeTestCase testing a PythonScript object in the default fixture

Note that you are encouraged to call any of the following methods
from your own tests to modify the test user's security credentials:

  - setRoles()
  - setPermissions()
  - login()
  - logout()

$Id: testPythonScript.py,v 1.9 2004/04/09 12:38:37 shh42 Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from AccessControl import Unauthorized
from AccessControl import getSecurityManager

ZopeTestCase.installProduct('PythonScripts')

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

    # Test the fixture ##############################################

    def testFixture(self):
        # The PythonScript should exist and be properly set up
        self.failUnless(hasattr(self.folder, 'ps'))
        self.assertEqual(self.ps.body(), ps_body1+'\n')
        self.assertEqual(self.ps.params(), ps_params1)
        owner = self.ps.getOwner()
        self.assertEqual(owner.getUserName(), ZopeTestCase.user_name)

    # Test the scripts ##############################################

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
        # PythonScript should raise a TypeError
        self.ps.ZPythonScript_edit(ps_params2, ps_body2)
        self.assertRaises(TypeError, self.ps, ())

    # Test access protection ########################################

    def testCannotAccessWithoutAccessPermission(self):
        # manage_main should be protected
        self.assertRaises(Unauthorized, self.ps.restrictedTraverse, 'manage_main')

    def testCanAccessWithAccessPermission(self):
        # manage_main should be accessible
        self.setPermissions(access_permissions)
        try:
            self.ps.restrictedTraverse('manage_main')
        except Unauthorized:
            self.fail('Access to manage_main was denied')

    def testCannotAccessIfAnonymous(self):
        # manage_main should be protected
        self.logout()
        self.assertRaises(Unauthorized, self.ps.restrictedTraverse, 'manage_main')

    def testCanAccessIfManager(self):
        # manage_main should be accessible to Managers
        self.setRoles(['Manager'])
        try:
            self.ps.restrictedTraverse('manage_main')
        except Unauthorized:
            self.fail('Access to manage_main was denied to Manager')

    # Test access protection with SecurityManager ###################

    def testCannotAccessWithoutAccessPermissionSecurityManager(self):
        # manage_main should be protected
        self.assertRaises(Unauthorized, getSecurityManager().validateValue, self.ps.manage_main)

    def testCanAccessWithAccessPermissionSecurityManager(self):
        # manage_main should be accessible
        self.setPermissions(access_permissions)
        try:
            getSecurityManager().validateValue(self.ps.manage_main)
        except Unauthorized:
            self.fail('Access to manage_main was denied')

    def testCannotAccessIfAnonymousSecurityManager(self):
        # manage_main should be protected
        self.logout()
        self.assertRaises(Unauthorized, getSecurityManager().validateValue, self.ps.manage_main)

    def testCanAccessIfManagerSecurityManager(self):
        # manage_main should be accessible to Managers
        self.setRoles(['Manager'])
        try:
            getSecurityManager().validateValue(self.ps.manage_main)
        except Unauthorized:
            self.fail('Access to manage_main was denied to Manager')

    # Test edit protection ##########################################

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
        # PythonScript should be editable
        self.setPermissions(change_permissions)
        try:
            self.ps.restrictedTraverse('ZPythonScript_edit')(ps_params2, ps_body2)
        except Unauthorized:
            self.fail('Access to ZPythonScript_edit was denied')
        else:
            self.assertEqual(self.ps.body(), ps_body2+'\n')
            self.assertEqual(self.ps.params(), ps_params2)

    def testCannotEditIfAnonymous(self):
        # PythonScript should not be editable
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
        # PythonScript should be editable for Managers
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

if __name__ == '__main__':
    framework()

