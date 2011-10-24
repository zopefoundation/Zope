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


class BasicUserTests(unittest.TestCase):

    def _getTargetClass(self):
        from AccessControl.User import BasicUser
        return BasicUser

    def _makeOne(self, name, password, roles, domains):
        return self._getTargetClass()(name, password, roles, domains)

    def _makeDerived(self, **kw):
        class Derived(self._getTargetClass()):
            def __init__(self, **kw):
                self.name = 'name'
                self.password = 'password'
                self.roles = ['Manager']
                self.domains = []
                self.__dict__.update(kw)
        return Derived(**kw)

    def test_ctor_is_abstract(self):
        # Subclasses must override __init__, and mustn't call the base version.
        self.assertRaises(NotImplementedError,
                          self._makeOne, 'name', 'password', ['Manager'], [])

    def test_abstract_methods(self):
        # Subclasses must override these methods.
        derived = self._makeDerived()
        self.assertRaises(NotImplementedError, derived.getUserName)
        self.assertRaises(NotImplementedError, derived.getId)
        self.assertRaises(NotImplementedError, derived._getPassword)
        self.assertRaises(NotImplementedError, derived.getRoles)
        self.assertRaises(NotImplementedError, derived.getDomains)

    # TODO: def test_getRolesInContext (w/wo local, callable, aq)
    # TODO: def test_authenticate (w/wo domains)
    # TODO: def test_allowed (...)
    # TODO: def test_has_role (w/wo str, context)
    # TODO: def test_has_permission (w/wo str)

    def test___len__(self):
        derived = self._makeDerived()
        self.assertEqual(len(derived), 1)

    def test___str__(self):
        derived = self._makeDerived(getUserName=lambda: 'phred')
        self.assertEqual(str(derived), 'phred')

    def test___repr__(self):
        derived = self._makeDerived(getUserName=lambda: 'phred')
        self.assertEqual(repr(derived), "<Derived 'phred'>")


class SimpleUserTests(unittest.TestCase):

    def _getTargetClass(self):
        from AccessControl.User import SimpleUser
        return SimpleUser

    def _makeOne(self, name='admin', password='123', roles=None, domains=None):
        if roles is None:
            roles = ['Manager']
        if domains is None:
            domains = []
        return self._getTargetClass()(name, password, roles, domains)

    def test_overrides(self):
        simple = self._makeOne()
        self.assertEqual(simple.getUserName(), 'admin')
        self.assertEqual(simple.getId(), 'admin')
        self.assertEqual(simple._getPassword(), '123')
        self.assertEqual(simple.getDomains(), ())

    def test_getRoles_anonymous(self):
        simple = self._makeOne('Anonymous User', roles=())
        self.assertEqual(simple.getRoles(), ())

    def test_getRoles_non_anonymous(self):
        simple = self._makeOne('phred', roles=())
        self.assertEqual(simple.getRoles(), ('Authenticated',))

    def test___repr__(self):
        special = self._makeOne()
        self.assertEqual(repr(special), "<SimpleUser 'admin'>")


class SpecialUserTests(unittest.TestCase):

    def _getTargetClass(self):
        from AccessControl.User import SpecialUser
        return SpecialUser

    def _makeOne(self, name='admin', password='123', roles=None, domains=None):
        if roles is None:
            roles = ['Manager']
        if domains is None:
            domains = []
        return self._getTargetClass()(name, password, roles, domains)

    def test_overrides(self):
        special = self._makeOne()
        self.assertEqual(special.getUserName(), 'admin')
        self.assertEqual(special.getId(), None)
        self.assertEqual(special._getPassword(), '123')
        self.assertEqual(special.getDomains(), ())

    def test___repr__(self):
        special = self._makeOne()
        self.assertEqual(repr(special), "<SpecialUser 'admin'>")


class UnrestrictedUserTests(unittest.TestCase):

    def _getTargetClass(self):
        from AccessControl.User import UnrestrictedUser
        return UnrestrictedUser

    def _makeOne(self, name='admin', password='123', roles=None, domains=None):
        if roles is None:
            roles = ['Manager']
        if domains is None:
            domains = []
        return self._getTargetClass()(name, password, roles, domains)

    def test_allowed__what_not_even_god_should_do(self):
        from AccessControl.PermissionRole import _what_not_even_god_should_do
        unrestricted = self._makeOne()
        self.failIf(unrestricted.allowed(self, _what_not_even_god_should_do))

    def test_allowed_empty(self):
        unrestricted = self._makeOne()
        self.failUnless(unrestricted.allowed(self, ()))

    def test_allowed_other(self):
        unrestricted = self._makeOne()
        self.failUnless(unrestricted.allowed(self, ('Manager',)))

    def test_has_role_empty_no_object(self):
        unrestricted = self._makeOne()
        self.failUnless(unrestricted.has_role(()))

    def test_has_role_empty_w_object(self):
        unrestricted = self._makeOne()
        self.failUnless(unrestricted.has_role((), self))

    def test_has_role_other_no_object(self):
        unrestricted = self._makeOne()
        self.failUnless(unrestricted.has_role(('Manager',)))

    def test_has_role_other_w_object(self):
        unrestricted = self._makeOne()
        self.failUnless(unrestricted.has_role(('Manager',), self))

    def test___repr__(self):
        unrestricted = self._makeOne()
        self.assertEqual(repr(unrestricted),
                         "<UnrestrictedUser 'admin'>")


class NullUnrestrictedUserTests(unittest.TestCase):

    def _getTargetClass(self):
        from AccessControl.User import NullUnrestrictedUser
        return NullUnrestrictedUser

    def _makeOne(self):
        return self._getTargetClass()()

    def test_overrides(self):
        simple = self._makeOne()
        self.assertEqual(simple.getUserName(), (None, None))
        self.assertEqual(simple.getId(), None)
        self.assertEqual(simple._getPassword(), (None, None))
        self.assertEqual(simple.getRoles(), ())
        self.assertEqual(simple.getDomains(), ())

    def test_getRolesInContext(self):
        null = self._makeOne()
        self.assertEqual(null.getRolesInContext(self), ())

    def test_authenticate(self):
        null = self._makeOne()
        self.failIf(null.authenticate('password', {}))

    def test_allowed(self):
        null = self._makeOne()
        self.failIf(null.allowed(self, ()))

    def test_has_role(self):
        null = self._makeOne()
        self.failIf(null.has_role('Authenticated'))

    def test_has_role_w_object(self):
        null = self._makeOne()
        self.failIf(null.has_role('Authenticated', self))

    def test_has_permission(self):
        null = self._makeOne()
        self.failIf(null.has_permission('View', self))

    def test___repr__(self):
        null = self._makeOne()
        self.assertEqual(repr(null), "<NullUnrestrictedUser (None, None)>")

    def test___str__(self):
        # See https://bugs.launchpad.net/zope2/+bug/142563
        null = self._makeOne()
        self.assertEqual(str(null), "<NullUnrestrictedUser (None, None)>")


# TODO class Test_readUserAccessFile(unittest.TestCase)


class BasicUserFolderTests(unittest.TestCase):
 
    def _getTargetClass(self):
        from AccessControl.User import BasicUserFolder
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


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(BasicUserTests),
        unittest.makeSuite(SimpleUserTests),
        unittest.makeSuite(SpecialUserTests),
        unittest.makeSuite(UnrestrictedUserTests),
        unittest.makeSuite(NullUnrestrictedUserTests),
        unittest.makeSuite(BasicUserFolderTests),
        unittest.makeSuite(UserFolderTests),
    ))
