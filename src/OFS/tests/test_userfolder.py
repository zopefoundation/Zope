##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for OFS.userfolder
"""
import unittest

# TODO class Test_readUserAccessFile(unittest.TestCase)


class BasicUserFolderTests(unittest.TestCase):
 
    def _getTargetClass(self):
        from OFS.userfolder import BasicUserFolder
        return BasicUserFolder
 
    def test_manage_users_security_initialized(self):
        uf = self._getTargetClass()()
        self.assertTrue(hasattr(uf, 'manage_users__roles__'))


class UserFolderTests(unittest.TestCase):

    def setUp(self):
        import transaction
        transaction.begin()

    def tearDown(self):
        import transaction
        from AccessControl.SecurityManagement import noSecurityManager
        noSecurityManager()
        transaction.abort()

    def _getTargetClass(self):
        from OFS.userfolder import UserFolder
        return UserFolder

    def _makeOne(self, app=None):
        if app is None:
            app = self._makeApp()
        uf = self._getTargetClass()().__of__(app)
        uf._doAddUser('user1', 'secret', ['role1'], [])
        return uf

    def _makeApp(self):
        from Testing.makerequest import makerequest
        from Testing.ZopeTestCase import ZopeLite
        app = makerequest(ZopeLite.app())
        # Set up a user and role
        app._addRole('role1')
        app.manage_role('role1', ['View'])
        # Set up a published object accessible to user
        app.addDTMLMethod('doc', file='')
        app.doc.manage_permission('View', ['role1'], acquire=0)
        # Rig the REQUEST so it looks like we traversed to doc
        app.REQUEST.set('PUBLISHED', app.doc)
        app.REQUEST.set('PARENTS', [app])
        app.REQUEST.steps = ['doc']
        return app

    def _makeBasicAuthToken(self, creds='user1:secret'):
        import base64
        return 'Basic %s' % base64.encodestring(creds)

    def _login(self, uf, name):
        from AccessControl.SecurityManagement import newSecurityManager
        user = uf.getUserById(name)
        user = user.__of__(uf)
        newSecurityManager(None, user)

    def test_class_conforms_to_IStandardUserFolder(self):
        from AccessControl.interfaces import IStandardUserFolder
        from zope.interface.verify import verifyClass
        verifyClass(IStandardUserFolder, self._getTargetClass())

    def testGetRolesInContext(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        app.manage_addLocalRoles('user1', ['Owner'])
        roles = user.getRolesInContext(app)
        self.assertTrue('role1' in roles)
        self.assertTrue('Owner' in roles)

    def testHasRole(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        self.assertTrue(user.has_role('role1', app))

    def testHasLocalRole(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        app.manage_addLocalRoles('user1', ['Owner'])
        self.assertTrue(user.has_role('Owner', app))

    def testHasPermission(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        self.assertTrue(user.has_permission('View', app))
        app.manage_role('role1', ['Add Folders'])
        self.assertTrue(user.has_permission('Add Folders', app))

    def testHasLocalRolePermission(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        app.manage_role('Owner', ['Add Folders'])
        app.manage_addLocalRoles('user1', ['Owner'])
        self.assertTrue(user.has_permission('Add Folders', app))
        
    def testAuthenticate(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        self.assertTrue(user.authenticate('secret', app.REQUEST))

    def testValidate(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.validate(app.REQUEST, self._makeBasicAuthToken(),
                           ['role1'])
        self.assertNotEqual(user, None)
        self.assertEqual(user.getUserName(), 'user1')

    def testNotValidateWithoutAuth(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.validate(app.REQUEST, '', ['role1'])
        self.assertEqual(user, None)

    def testValidateWithoutRoles(self):
        # Note - calling uf.validate without specifying roles will cause
        # the security machinery to determine the needed roles by looking
        # at the object itself (or its container). I'm putting this note
        # in to clarify because the original test expected failure but it
        # really should have expected success, since the user and the
        # object being checked both have the role 'role1', even though no
        # roles are passed explicitly to the userfolder validate method.
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.validate(app.REQUEST, self._makeBasicAuthToken())
        self.assertEqual(user.getUserName(), 'user1')

    def testNotValidateWithEmptyRoles(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.validate(app.REQUEST, self._makeBasicAuthToken(), [])
        self.assertEqual(user, None)

    def testNotValidateWithWrongRoles(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.validate(app.REQUEST, self._makeBasicAuthToken(),
                           ['Manager'])
        self.assertEqual(user, None)

    def testAllowAccessToUser(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        self._login(uf, 'user1')
        app.restrictedTraverse('doc')

    def testDenyAccessToAnonymous(self):
        from AccessControl import Unauthorized
        app = self._makeApp()
        self.assertRaises(Unauthorized, app.restrictedTraverse, 'doc')


def test_suite():
    suite = unittest.TestSuite((
        unittest.makeSuite(BasicUserFolderTests),
        unittest.makeSuite(UserFolderTests),
    ))
    return suite
