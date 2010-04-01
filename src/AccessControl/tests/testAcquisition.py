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
"""Tests demonstrating consequences of guarded_getattr fix from 2004/08/07

   http://mail.zope.org/pipermail/zope-checkins/2004-August/028152.html
   http://zope.org/Collectors/CMF/259

"""

import unittest

from Testing.makerequest import makerequest

import Zope2
Zope2.startup()

from OFS.SimpleItem import SimpleItem
from App.class_init import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.Permissions import view, view_management_screens
from AccessControl.ImplPython import guarded_getattr as guarded_getattr_py
from AccessControl.ImplC import guarded_getattr as guarded_getattr_c
from Products.SiteErrorLog.SiteErrorLog import SiteErrorLog


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

class ProtectedSiteErrorLog(SiteErrorLog):
    '''This differs from the base by declaring security
       for the object itself.
    '''
    id = 'error_log2'
    security = ClassSecurityInfo()
    security.declareObjectProtected(view)

InitializeClass(ProtectedSiteErrorLog)


class TestGetAttr(unittest.TestCase):

    def setUp(self):
        import transaction
        self.guarded_getattr = guarded_getattr_py
        transaction.manager.begin()
        self.app = makerequest(Zope2.app())
        try:

            # Set up a manager user
            self.uf = self.app.acl_users
            self.uf._doAddUser('manager', 'secret', ['Manager'], [])
            self.login('manager')

            # Set up objects in the root that we want to aquire
            self.app.manage_addFolder('plain_folder')
            self.app._setObject('error_log2', ProtectedSiteErrorLog())

            # We also want to be able to acquire simple attributes
            self.app.manage_addProperty(id='simple_type', type='string', value='a string')

            # Set up a subfolder and the objects we want to acquire from
            self.app.manage_addFolder('subfolder')
            self.folder = self.app.subfolder
            self.folder._setObject('allowed', AllowedItem())
            self.folder._setObject('denied', DeniedItem())
            self.folder._setObject('protected', ProtectedItem())

        except:
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
        # XXX: Fails in 2.7.3
        o = self.guarded_getattr(self.folder.denied, 'acl_users')
        self.assertEqual(o, self.app.acl_users)

    def testAclUsersProtected(self):
        # XXX: Fails in 2.7.3 for Anonymous
        o = self.guarded_getattr(self.folder.protected, 'acl_users')
        self.assertEqual(o, self.app.acl_users)

    # Acquire browser id manager

    def testBrowserIdManagerAllowed(self):
        o = self.guarded_getattr(self.folder.allowed, 'browser_id_manager')
        self.assertEqual(o, self.app.browser_id_manager)

    def testBrowserIdManagerDenied(self):
        o = self.guarded_getattr(self.folder.denied, 'browser_id_manager')
        self.assertEqual(o, self.app.browser_id_manager)

    def testBrowserIdManagerProtected(self):
        o = self.guarded_getattr(self.folder.protected, 'browser_id_manager')
        self.assertEqual(o, self.app.browser_id_manager)

    # Acquire error log

    def testErrorLogAllowed(self):
        o = self.guarded_getattr(self.folder.allowed, 'error_log')
        self.assertEqual(o, self.app.error_log)

    def testErrorLogDenied(self):
        # XXX: Fails in 2.7.3
        o = self.guarded_getattr(self.folder.denied, 'error_log')
        self.assertEqual(o, self.app.error_log)

    def testErrorLogProtected(self):
        # XXX: Fails in 2.7.3 for Anonymous
        o = self.guarded_getattr(self.folder.protected, 'error_log')
        self.assertEqual(o, self.app.error_log)

    # Now watch this: error log with object security declaration works fine!

    def testProtectedErrorLogAllowed(self):
        o = self.guarded_getattr(self.folder.allowed, 'error_log2')
        self.assertEqual(o, self.app.error_log2)

    def testProtectedErrorLogDenied(self):
        o = self.guarded_getattr(self.folder.denied, 'error_log2')
        self.assertEqual(o, self.app.error_log2)

    def testProtectedErrorLogProtected(self):
        o = self.guarded_getattr(self.folder.protected, 'error_log2')
        self.assertEqual(o, self.app.error_log2)

    # This appears to mean that any potential acquiree must make sure
    # to declareObjectProtected(SomePermission).

    # From the ZDG:
    # We've seen how to make  assertions on methods - but in the case of
    # someObject we are not trying to access any particular method, but
    # rather the object itself (to pass it to some_method). Because the
    # security machinery will try to validate access to someObject, we
    # need a way to let the security machinery know how to handle access
    # to the object itself in addition to protecting its methods.

    # IOW, acquiring an object in restricted Python now amounts to
    # "passing it to some_method".


    # Also test Richard Jones' use-case of acquiring a string:

    def testSimpleTypeAllowed(self):
        o = self.guarded_getattr(self.folder.allowed, 'simple_type')
        self.assertEqual(o, 'a string')

    def testSimpleTypeDenied(self):
        # XXX: Fails in 2.7.3
        o = self.guarded_getattr(self.folder.denied, 'simple_type')
        self.assertEqual(o, 'a string')

    def testSimpleTypeProtected(self):
        # XXX: Fails in 2.7.3 for Anonymous
        o = self.guarded_getattr(self.folder.protected, 'simple_type')
        self.assertEqual(o, 'a string')


class TestGetAttrAnonymous(TestGetAttr):

    # Run all tests again as Anonymous User

    def setUp(self):
        TestGetAttr.setUp(self)
        # Log out
        noSecurityManager()


class TestGetAttr_c(TestGetAttr):

    def setUp(self):
        TestGetAttr.setUp(self)
        self.guarded_getattr = guarded_getattr_c

class TestGetAttrAnonymous_c(TestGetAttrAnonymous):

    def setUp(self):
        TestGetAttrAnonymous.setUp(self)
        self.guarded_getattr = guarded_getattr_c


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestGetAttr))
    suite.addTest(unittest.makeSuite(TestGetAttrAnonymous))
    suite.addTest(unittest.makeSuite(TestGetAttr_c))
    suite.addTest(unittest.makeSuite(TestGetAttrAnonymous_c))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

