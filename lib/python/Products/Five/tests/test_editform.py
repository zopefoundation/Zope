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
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.Five.tests.fivetest import *

from AccessControl import Unauthorized
from zope.app.form.browser.submit import Update

from Products.Five.tests.products.FiveTest.simplecontent import manage_addFieldSimpleContent
from Products.Five.tests.products.FiveTest.helpers import manage_addFiveTraversableFolder
from Products.Five.tests.products.FiveTest.schemacontent import manage_addComplexSchemaContent


class EditFormTest(Functional, FiveTestCase):

    def afterSetUp(self):
        manage_addFieldSimpleContent(self.folder, 'edittest', 'Test')
        uf = self.folder.acl_users
        uf._doAddUser('viewer', 'secret', [], [])
        uf._doAddUser('manager', 'r00t', ['Manager'], [])

    def test_editform(self):
        response = self.publish('/test_folder_1_/edittest/edit.html',
                                basic='manager:r00t')
        # we're using a GET request to post variables, but seems to be
        # the easiest..
        response = self.publish(
            '/test_folder_1_/edittest/edit.html?%s=1&field.title=FooTitle&field.description=FooDescription' % Update,
            basic='manager:r00t')
        self.assertEquals('FooTitle', self.folder.edittest.title)
        self.assertEquals('FooDescription', self.folder.edittest.description)

    def test_editform_invalid(self):
        # missing title, which is required
        self.folder.edittest.description = ''

        response = self.publish(
            '/test_folder_1_/edittest/edit.html?%s=1&field.title=&field.description=BarDescription' % Update,
            basic='manager:r00t')
        # we expect that we get a 200 Ok
        self.assertEqual(200, response.getStatus())
        self.assertEquals('Test', self.folder.edittest.title)
        self.assertEquals('', self.folder.edittest.description)

    def test_addform(self):
        manage_addFiveTraversableFolder(self.folder, 'ftf')
        self.folder = self.folder.ftf
        response = self.publish('/test_folder_1_/ftf/+/addsimplecontent.html',
                                basic='manager:r00t')
        self.assertEquals(200, response.getStatus())
        # we're using a GET request to post variables, but seems to be
        # the easiest..
        response = self.publish(
            '/test_folder_1_/ftf/+/addsimplecontent.html?%s=1&add_input_name=alpha&field.title=FooTitle&field.description=FooDescription' % Update,
            basic='manager:r00t')
        # we expect to get a 302 (redirect)
        self.assertEquals(302, response.getStatus())
        # we expect the object to be there with the right id
        self.assertEquals('alpha', self.folder.alpha.id)
        self.assertEquals('FooTitle', self.folder.alpha.title)
        self.assertEquals('FooDescription', self.folder.alpha.description)

    def test_objectWidget(self):
        manage_addComplexSchemaContent(self.folder, 'csc')
        response = self.publish('/test_folder_1_/csc/edit.html',
                                basic='manager:r00t')
        self.assertEquals(200, response.getStatus())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(EditFormTest))
    return suite

if __name__ == '__main__':
    framework()

