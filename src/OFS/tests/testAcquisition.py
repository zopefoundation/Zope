##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import unittest

import Zope2
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.ZopeGuards import guarded_getattr
from OFS.SimpleItem import SimpleItem
from Testing.makerequest import makerequest


Zope2.startup_wsgi()


class AllowedItem(SimpleItem):
    id = 'allowed'
    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')


InitializeClass(AllowedItem)


class DeniedItem(SimpleItem):
    id = 'denied'
    security = ClassSecurityInfo()
    security.setDefaultAccess('deny')


InitializeClass(DeniedItem)


class ProtectedItem(SimpleItem):
    id = 'protected'
    security = ClassSecurityInfo()
    security.declareObjectProtected(view_management_screens)


InitializeClass(ProtectedItem)


class TestGetAttr(unittest.TestCase):

    def setUp(self):
        import transaction
        self.guarded_getattr = guarded_getattr
        transaction.manager.begin()
        self.app = makerequest(Zope2.app())
        try:

            # Set up a manager user
            self.uf = self.app.acl_users
            self.uf._doAddUser('manager', 'secret', ['Manager'], [])
            self.login('manager')

            # Set up objects in the root that we want to aquire
            self.app.manage_addFolder('plain_folder')

            # We also want to be able to acquire simple attributes
            self.app.manage_addProperty(
                id='simple_type', type='string', value='a string')

            # Set up a subfolder and the objects we want to acquire from
            self.app.manage_addFolder('subfolder')
            self.folder = self.app.subfolder
            self.folder._setObject('allowed', AllowedItem())
            self.folder._setObject('denied', DeniedItem())
            self.folder._setObject('protected', ProtectedItem())

        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        import transaction
        noSecurityManager()
        transaction.manager.get().abort()
        self.app._p_jar.close()

    def login(self, name):
        user = self.uf.getUserById(name)
        user = user.__of__(self.uf)
        newSecurityManager(None, user)

    # Acquire plain folder

    def testFolderAllowed(self):
        o = self.guarded_getattr(self.folder.allowed, 'plain_folder')
        self.assertEqual(o, self.app.plain_folder)

    def testFolderDenied(self):
        o = self.guarded_getattr(self.folder.denied, 'plain_folder')
        self.assertEqual(o, self.app.plain_folder)

    def testFolderProtected(self):
        o = self.guarded_getattr(self.folder.protected, 'plain_folder')
        self.assertEqual(o, self.app.plain_folder)

    # Acquire user folder

    def testAclUsersAllowed(self):
        o = self.guarded_getattr(self.folder.allowed, 'acl_users')
        self.assertEqual(o, self.app.acl_users)

    def testAclUsersDenied(self):
        o = self.guarded_getattr(self.folder.denied, 'acl_users')
        self.assertEqual(o, self.app.acl_users)

    def testAclUsersProtected(self):
        o = self.guarded_getattr(self.folder.protected, 'acl_users')
        self.assertEqual(o, self.app.acl_users)

    # Also test Richard Jones' use-case of acquiring a string:

    def testSimpleTypeAllowed(self):
        o = self.guarded_getattr(self.folder.allowed, 'simple_type')
        self.assertEqual(o, 'a string')

    def testSimpleTypeDenied(self):
        o = self.guarded_getattr(self.folder.denied, 'simple_type')
        self.assertEqual(o, 'a string')

    def testSimpleTypeProtected(self):
        o = self.guarded_getattr(self.folder.protected, 'simple_type')
        self.assertEqual(o, 'a string')


class TestGetAttrAnonymous(TestGetAttr):
    # Run all tests again as Anonymous User

    def setUp(self):
        TestGetAttr.setUp(self)
        # Log out
        noSecurityManager()
