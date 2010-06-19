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
        from AccessControl.users import BasicUser
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
        from AccessControl.users import SimpleUser
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
        from AccessControl.users import SpecialUser
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
        from AccessControl.users import UnrestrictedUser
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
        from AccessControl.users import NullUnrestrictedUser
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicUserTests))
    suite.addTest(unittest.makeSuite(SimpleUserTests))
    suite.addTest(unittest.makeSuite(SpecialUserTests))
    suite.addTest(unittest.makeSuite(UnrestrictedUserTests))
    suite.addTest(unittest.makeSuite(NullUnrestrictedUserTests))
    return suite
