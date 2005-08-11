##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Test security from restricted Python interpreter

$Id: test_security2.py 12915 2005-05-31 10:23:19Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.Five.tests.fivetest import *
from Products.Five.tests.products.FiveTest.helpers import manage_addFiveTraversableFolder

from AccessControl import getSecurityManager
from AccessControl import Unauthorized

import glob
from Products.Five.tests.products import FiveTest
_prefix = os.path.dirname(FiveTest.__file__)
dir_resource_names = [os.path.basename(r)
                      for r in (glob.glob('%s/*.png' % _prefix) +
                                glob.glob('%s/*.pt' % _prefix) +
                                glob.glob('%s/[a-z]*.py' % _prefix) +
                                glob.glob('%s/*.css' % _prefix))]

ViewManagementScreens = 'View management screens'

from Products.Five.tests.products.FiveTest.simplecontent import manage_addSimpleContent


class RestrictedPythonTest(FiveTestCase):
    """
    Test whether code is really restricted

    Kind permission from Plone to use this.
    """

    def addPS(self, id, params='', body=''):
        # clean up any 'ps' that's already here..
        try:
            self.folder._getOb(id)
            self.folder.manage_delObjects([id])
        except AttributeError:
            pass # it's okay, no 'ps' exists yet
        factory = self.folder.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript(id)
        self.folder[id].ZPythonScript_edit(params, body)

    def check(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (ImportError, Unauthorized), e:
            self.fail(e)

    def checkUnauthorized(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (AttributeError, Unauthorized):
            pass
        else:
            self.fail("Authorized but shouldn't be")


view_names = [
    'eagle.txt',
    'falcon.html',
    'owl.html',
    'flamingo.html',
    'flamingo2.html',
    'condor.html',
    'protectededitform.html']

public_view_names = [
    'public_attribute_page',
    'public_template_page',
    'public_template_class_page']

resource_names = [
    'cockatiel.html',
    'style.css',
    'pattern.png'
    ]


class SecurityTest(RestrictedPythonTest):

    def afterSetUp(self):
        manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
        uf = self.folder.acl_users
        uf._doAddUser('viewer', 'secret', [], [])
        uf._doAddUser('manager', 'r00t', ['Manager'], [])

    def test_no_permission(self):
        self.login('viewer')
        for view_name in view_names:
            self.checkUnauthorized(
                'context.restrictedTraverse("testoid/%s")()' % view_name)

    def test_resource_no_permission(self):
        self.login('viewer')
        for resource in resource_names:
            self.checkUnauthorized(
                'context.restrictedTraverse("testoid/++resource++%s")()' %
                resource)

    def test_directory_resource_no_permission(self):
        self.login('viewer')
        base = 'testoid/++resource++fivetest_resources/%s'
        for resource in dir_resource_names:
            path = base % resource
            self.checkUnauthorized(
                'context.restrictedTraverse("%s")' % path)

    def test_permission(self):
        self.login('manager')
        for view_name in view_names:
            self.check(
                'context.restrictedTraverse("testoid/%s")()' % view_name)

    def test_resource_permission(self):
        self.login('manager')
        for resource in resource_names:
            self.check(
                'context.restrictedTraverse("testoid/++resource++%s")()' %
                resource)

    def test_directory_resource_permission(self):
        self.login('manager')
        base = 'testoid/++resource++fivetest_resources/%s'
        for resource in dir_resource_names:
            path = base % resource
            self.check(
                'context.restrictedTraverse("%s")' % path)

    def test_public_permission(self):
        self.logout()
        for view_name in public_view_names:
            self.check(
                'context.restrictedTraverse("testoid/%s")()' % view_name)

    def test_view_method_permission(self):
        self.login('manager')
        self.check(
            'context.restrictedTraverse("testoid/eagle.method").eagle()')


class PublishTest(Functional, FiveTestCase):
    """A functional test for security actually involving the publisher.
    """
    def afterSetUp(self):
        manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
        uf = self.folder.acl_users
        uf._doAddUser('viewer', 'secret', [], [])
        uf._doAddUser('manager', 'r00t', ['Manager'], [])

    def test_no_permission(self):
        for view_name in view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name,
                                    basic='viewer:secret')
            # we expect that we get a 401 Unauthorized
            status = response.getStatus()
            self.failUnless(status == 401, (status, 401, view_name))

    def test_all_permissions(self):
        permissions = self.folder.possible_permissions()
        self.folder._addRole('Viewer')
        self.folder.manage_role('Viewer', permissions)
        self.folder.manage_addLocalRoles(
            'viewer', ['Viewer'])

        for view_name in view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name,
                                    basic='viewer:secret')
            status = response.getStatus()
            self.failUnless(status == 200, (status, 200, view_name))

    def test_almost_all_permissions(self):
        permissions = self.folder.possible_permissions()
        permissions.remove(ViewManagementScreens)
        self.folder._addRole('Viewer')
        self.folder.manage_role('Viewer', permissions)
        self.folder.manage_addLocalRoles(
            'viewer', ['Viewer'])

        for view_name in view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name,
                                    basic='viewer:secret')
            # we expect that we get a 401 Unauthorized
            status = response.getStatus()
            self.failUnless(status == 401, (status, 401, view_name))

    def test_manager_permission(self):
        for view_name in view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name,
                                    basic='manager:r00t')
            # we expect that we get a 200 Ok
            self.assertEqual(response.getStatus(), 200)

    def test_public_permission(self):
        for view_name in public_view_names:
            response = self.publish('/test_folder_1_/testoid/%s' % view_name)
            status = response.getStatus()
            self.failUnless(status == 200, (status, 200, view_name))

    def test_addpages(self):
        manage_addFiveTraversableFolder(self.folder, 'ftf')

        # Unprotected as anonymous
        response = self.publish('/test_folder_1_/ftf/+/addfieldcontent.html')
        self.assertEqual(response.getStatus(), 200)

        # Protected as manager
        response = self.publish('/test_folder_1_/ftf/+/protectedaddform.html',
                                    basic='manager:r00t')
        self.assertEqual(response.getStatus(), 200)

        # Protected as user
        response = self.publish('/test_folder_1_/ftf/+/protectedaddform.html',
                                    basic='viewer:secret')
        self.assertEqual(response.getStatus(), 401)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(SecurityTest))
    suite.addTest(makeSuite(PublishTest))
    return suite

if __name__ == '__main__':
    framework()
