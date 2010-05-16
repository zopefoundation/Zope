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
""" Unit tests for AccessControl.User
"""
import unittest


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
        from AccessControl.User import UserFolder
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

    def testGetUser(self):
        uf = self._makeOne()
        self.failIfEqual(uf.getUser('user1'), None)

    def testGetBadUser(self):
        uf = self._makeOne()
        self.assertEqual(uf.getUser('user2'), None)

    def testGetUserById(self):
        uf = self._makeOne()
        self.failIfEqual(uf.getUserById('user1'), None)

    def testGetBadUserById(self):
        uf = self._makeOne()
        self.assertEqual(uf.getUserById('user2'), None)

    def testGetUsers(self):
        uf = self._makeOne()
        users = uf.getUsers()
        self.failUnless(users)
        self.assertEqual(users[0].getUserName(), 'user1')

    def testGetUserNames(self):
        uf = self._makeOne()
        names = uf.getUserNames()
        self.failUnless(names)
        self.assertEqual(names[0], 'user1')

    def testIdentify(self):
        uf = self._makeOne()
        name, password = uf.identify(self._makeBasicAuthToken())
        self.assertEqual(name, 'user1')
        self.assertEqual(password, 'secret')

    def testGetRoles(self):
        uf = self._makeOne()
        user = uf.getUser('user1')
        self.failUnless('role1' in user.getRoles())

    def testGetRolesInContext(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        app.manage_addLocalRoles('user1', ['Owner'])
        roles = user.getRolesInContext(app)
        self.failUnless('role1' in roles)
        self.failUnless('Owner' in roles)

    def testHasRole(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        self.failUnless(user.has_role('role1', app))

    def testHasLocalRole(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        app.manage_addLocalRoles('user1', ['Owner'])
        self.failUnless(user.has_role('Owner', app))

    def testHasPermission(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        self.failUnless(user.has_permission('View', app))
        app.manage_role('role1', ['Add Folders'])
        self.failUnless(user.has_permission('Add Folders', app))

    def testHasLocalRolePermission(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        app.manage_role('Owner', ['Add Folders'])
        app.manage_addLocalRoles('user1', ['Owner'])
        self.failUnless(user.has_permission('Add Folders', app))
        
    def testAuthenticate(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.getUser('user1')
        self.failUnless(user.authenticate('secret', app.REQUEST))

    def testValidate(self):
        app = self._makeApp()
        uf = self._makeOne(app)
        user = uf.validate(app.REQUEST, self._makeBasicAuthToken(),
                           ['role1'])
        self.failIfEqual(user, None)
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

    def testMaxListUsers(self):
        # create a folder-ish thing which contains a roleManager,
        # then put an acl_users object into the folde-ish thing
        from AccessControl.User import BasicUserFolder

        class Folderish(BasicUserFolder):
            def __init__(self, size, count):
                self.maxlistusers = size
                self.users = []
                self.acl_users = self
                self.__allow_groups__ = self
                for i in xrange(count):
                    self.users.append("Nobody")

            def getUsers(self):
                return self.users

            def user_names(self):
                return self.getUsers()


        tinyFolderOver = Folderish(15, 20)
        tinyFolderUnder = Folderish(15, 10)

        assert tinyFolderOver.maxlistusers == 15
        assert tinyFolderUnder.maxlistusers == 15
        assert len(tinyFolderOver.user_names()) == 20
        assert len(tinyFolderUnder.user_names()) == 10

        try:
            list = tinyFolderOver.get_valid_userids()
            assert 0, "Did not raise overflow error"
        except OverflowError:
            pass

        try:
            list = tinyFolderUnder.get_valid_userids()
            pass
        except OverflowError:
            assert 0, "Raised overflow error erroneously"

    def test__doAddUser_with_not_yet_encrypted_passwords(self):
        # See collector #1869 && #1926
        from AccessControl.AuthEncoding import pw_validate

        USER_ID = 'not_yet_encrypted'
        PASSWORD = 'password'

        uf = self._makeOne()
        uf.encrypt_passwords = True
        self.failIf(uf._isPasswordEncrypted(PASSWORD))

        uf._doAddUser(USER_ID, PASSWORD, [], [])
        user = uf.getUserById(USER_ID)
        self.failUnless(uf._isPasswordEncrypted(user.__))
        self.failUnless(pw_validate(user.__, PASSWORD))

    def test__doAddUser_with_preencrypted_passwords(self):
        # See collector #1869 && #1926
        from AccessControl.AuthEncoding import pw_validate

        USER_ID = 'already_encrypted'
        PASSWORD = 'password'

        uf = self._makeOne()
        uf.encrypt_passwords = True
        ENCRYPTED = uf._encryptPassword(PASSWORD)

        uf._doAddUser(USER_ID, ENCRYPTED, [], [])
        user = uf.getUserById(USER_ID)
        self.assertEqual(user.__, ENCRYPTED)
        self.failUnless(uf._isPasswordEncrypted(user.__))
        self.failUnless(pw_validate(user.__, PASSWORD))


class UserTests(unittest.TestCase):

    def _getTargetClass(self):
        from AccessControl.User import User
        return User

    def _makeOne(self, name, password, roles, domains):
        return self._getTargetClass()(name, password, roles, domains)

    def testGetUserName(self):
        f = self._makeOne('chris', '123', ['Manager'], [])
        self.assertEqual(f.getUserName(), 'chris')
        
    def testGetUserId(self):
        f = self._makeOne('chris', '123', ['Manager'], [])
        self.assertEqual(f.getId(), 'chris')

    def testBaseUserGetIdEqualGetName(self):
        # this is true for the default user type, but will not
        # always be true for extended user types going forward (post-2.6)
        f = self._makeOne('chris', '123', ['Manager'], [])
        self.assertEqual(f.getId(), f.getUserName())

    def testGetPassword(self):
        f = self._makeOne('chris', '123', ['Manager'], [])
        self.assertEqual(f._getPassword(), '123')

    def testGetRoles(self):
        f = self._makeOne('chris', '123', ['Manager'], [])
        self.assertEqual(f.getRoles(), ('Manager', 'Authenticated'))

    def testGetDomains(self):
        f = self._makeOne('chris', '123', ['Manager'], [])
        self.assertEqual(f.getDomains(), ())

    def testRepr(self):
        f = self._makeOne('flo', '123', ['Manager'], [])
        self.assertEqual(repr(f), "<User 'flo'>")

    def testReprSpecial(self):
        from AccessControl.User import NullUnrestrictedUser
        from AccessControl.User import nobody
        from AccessControl.User import system
        # NullUnrestrictedUser is used when there is no emergency user
        self.assertEqual(repr(NullUnrestrictedUser()),
                         "<NullUnrestrictedUser (None, None)>")
        self.assertEqual(repr(nobody),
                         "<SpecialUser 'Anonymous User'>")
        self.assertEqual(repr(system),
                         "<UnrestrictedUser 'System Processes'>")


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UserFolderTests))
    suite.addTest(unittest.makeSuite(UserTests))
    return suite
