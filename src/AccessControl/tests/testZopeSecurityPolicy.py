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

import os
import sys
import thread
import unittest

import ZODB
try:
    from zExceptions import Unauthorized
except ImportError:
    Unauthorized = 'Unauthorized'
from AccessControl.User import UserFolder
from AccessControl.SecurityManagement import SecurityContext
from Acquisition import Implicit, Explicit, aq_base
from MethodObject import Method
from ComputedAttribute import ComputedAttribute


user_roles = ('RoleOfUser',)
eo_roles = ('RoleOfExecutableOwner',)
sysadmin_roles = ('RoleOfSysAdmin',)


class App(Explicit):
    def unrestrictedTraverse(self, path):
        ob = self
        for el in path:
            ob = getattr(ob, el)
        return ob

class PublicMethod (Method):
    def getOwner(self):
        return None

    def __call__(*args, **kw):
        return args, kw

    def getWrappedOwner(self):
        return None

    __roles__ = None


class ProtectedMethod (PublicMethod):
    __roles__ = user_roles


class OwnedMethod (PublicMethod):
    __roles__ = eo_roles

    def getOwner(self):
        return self.aq_parent.aq_parent.acl_users.getUserById('theowner')

    def getWrappedOwner(self):
        acl_users = self.aq_parent.aq_parent.acl_users
        user = acl_users.getUserById('theowner')
        return user.__of__(acl_users)


class setuidMethod (PublicMethod):
    _proxy_roles = sysadmin_roles


class OwnedSetuidMethod(Implicit):
    __roles__ = eo_roles
    _proxy_roles = sysadmin_roles

    def getOwner(self, info=0):
        if info:
            return (('subobject', 'acl_users'), 'theowner')
        else:
            return self.aq_parent.aq_parent.acl_users.getUserById('theowner')

    def getWrappedOwner(self):
        acl_users = self.aq_parent.aq_parent.acl_users
        user = acl_users.getUserById('theowner')
        return user.__of__(acl_users)


class DangerousMethod (PublicMethod):
    # Only accessible to sysadmin or people who use proxy roles
    __roles__ = sysadmin_roles

class SimpleItemish (Implicit):
    public_m = PublicMethod()
    protected_m = ProtectedMethod()
    owned_m = OwnedMethod()
    setuid_m = setuidMethod()
    dangerous_m = DangerousMethod()
    public_prop = 'Public Value'
    private_prop = 'Private Value'

class ImplictAcqObject(Implicit):
    pass


class UnprotectedSimpleItem (SimpleItemish):

    __allow_access_to_unprotected_subobjects__ = 1


class UnprotectedSimpleItemBool (SimpleItemish):

    __allow_access_to_unprotected_subobjects__ = True


class OwnedSimpleItem(UnprotectedSimpleItem):
    def getOwner(self, info=0):
        if info:
            return (('subobject', 'acl_users'), 'theowner')
        else:
            return self.aq_parent.acl_users.getuserById('theowner')


class RestrictedSimpleItem (SimpleItemish):

    __allow_access_to_unprotected_subobjects__ = 0

    _Foo_Permission = user_roles + eo_roles
    _Kill_Permission = sysadmin_roles
    _View_Permission = eo_roles


class PartlyProtectedSimpleItem1 (SimpleItemish):

    __allow_access_to_unprotected_subobjects__ = {'public_prop': 1,}


class PartlyProtectedSimpleItem2 (SimpleItemish):

    def __allow_access_to_unprotected_subobjects__(self, name, value):
        if name == 'public_prop':
            return 1
        return 0


class PartlyProtectedSimpleItem3 (PartlyProtectedSimpleItem1):
    # Set the roles of objects that are accessible because of
    # __allow_access_to_unprotected_subobjects__ .
    __roles__ = sysadmin_roles


class SimpleClass:
    attr = 1


class ZopeSecurityPolicyTestBase(unittest.TestCase):

    def setUp(self):
        a = App()
        self.a = a
        a.item = UnprotectedSimpleItem()
        a.itemb = UnprotectedSimpleItemBool()
        self.item = a.item
        a.r_item = RestrictedSimpleItem()
        a.item1 = PartlyProtectedSimpleItem1()
        a.item2 = PartlyProtectedSimpleItem2()
        a.item3 = PartlyProtectedSimpleItem3()
        uf = UserFolder()
        a.acl_users = uf
        self.uf = a.acl_users
        uf._addUser('joe', 'password', 'password', user_roles, ())
        uf._addUser('theowner', 'password', 'password', eo_roles, ())
        user = uf.getUserById('joe')
        self.user = user
        context = SecurityContext(user)
        self.context = context
        self.policy = self._makeOne()

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def assertPolicyAllows(self, ob, attrname):
        res = self.policy.validate(ob, ob, attrname, getattr(ob, attrname),
                                   self.context)
        if not res:
            self.fail('Policy quietly denied %s' % attrname)

    def assertPolicyDenies(self, ob, attrname):
        try:
            res = self.policy.validate(ob, ob, attrname, getattr(ob, attrname),
                                       self.context)
        except Unauthorized:
            # Passed the test.
            pass
        else:
            if res:
                self.fail('Policy quietly allowed %s' % attrname)
            else:
                self.fail('Policy denied %s, but did not '
                          'throw an exception.' % attrname)

    def testUserAccess(self):
        item = self.item
        self.assertPolicyAllows(item, 'public_m')
        self.assertPolicyAllows(item, 'protected_m')
        self.assertPolicyDenies(item, 'owned_m')
        self.assertPolicyAllows(item, 'setuid_m')
        self.assertPolicyDenies(item, 'dangerous_m')

    def testOwnerAccess(self):
        self.context = SecurityContext(self.uf.getUserById('theowner'))
        item = self.item
        self.assertPolicyAllows(item, 'public_m')
        self.assertPolicyDenies(item, 'protected_m')
        self.assertPolicyAllows(item, 'owned_m')
        self.assertPolicyAllows(item, 'setuid_m')
        self.assertPolicyDenies(item, 'dangerous_m')

    def testProxyAccess(self):
        item = self.item
        self.context.stack.append(item.setuid_m)
        self.assertPolicyAllows(item, 'public_m')
        self.assertPolicyDenies(item, 'protected_m')
        self.assertPolicyDenies(item, 'owned_m')
        self.assertPolicyAllows(item, 'setuid_m')
        self.assertPolicyAllows(item, 'dangerous_m')

    def testIdentityProxy(self):
        eo = ImplictAcqObject()
        eo.getOwner = lambda: None
        self.context.stack.append(eo)
        rc = sys.getrefcount(eo)
        self.testUserAccess()
        self.assertEqual(rc, sys.getrefcount(eo))
        eo._proxy_roles = ()
        self.testUserAccess()
        self.assertEqual(rc, sys.getrefcount(eo))

    def testAccessToUnprotectedSubobjects(self):
        item = self.item
        itemb = self.a.itemb
        r_item = self.a.r_item
        item1 = self.a.item1
        item2 = self.a.item2
        item3 = self.a.item3
        self.assertPolicyAllows(item,  'public_prop')
        self.assertPolicyAllows(itemb, 'public_prop')
        self.assertPolicyDenies(r_item,'public_prop')
        self.assertPolicyAllows(item1, 'public_prop')
        self.assertPolicyAllows(item2, 'public_prop')
        self.assertPolicyDenies(item3,'public_prop')
        self.assertPolicyAllows(item,  'private_prop')
        self.assertPolicyDenies(r_item,'private_prop')
        self.assertPolicyDenies(item1, 'private_prop')
        self.assertPolicyDenies(item2, 'private_prop')
        self.assertPolicyDenies(item3, 'private_prop')

    def testAccessToSimpleContainer(self):
        self.assertPolicyAllows({}, 'keys')
        self.assertPolicyAllows([], 'append')
        self.assertPolicyDenies(SimpleClass, 'attr')
        self.assertPolicyDenies(SimpleClass(), 'attr')
        c = SimpleClass()
        c.attr = PublicMethod()
        self.assertPolicyAllows(c, 'attr')

    def testUnicodeAttributeLookups(self):
        item = self.item
        r_item = self.a.r_item
        self.assertPolicyAllows(item, u'public_prop')
        self.assertPolicyDenies(r_item, u'private_prop')
        self.assertPolicyAllows(item, u'public_m')
        self.assertPolicyDenies(item, u'dangerous_m')

    def testRolesForPermission(self):
        # Test of policy.checkPermission().
        r_item = self.a.r_item
        context = self.context
        v = self.policy.checkPermission('View', r_item, context)
        self.assert_(not v, '_View_Permission should deny access to user')
        o_context = SecurityContext(self.uf.getUserById('theowner'))
        v = self.policy.checkPermission('View', r_item, o_context)
        self.assert_(v, '_View_Permission should grant access to theowner')

    def test_checkPermission_respects_proxy_roles(self):
        r_item = self.a.r_item
        context = self.context
        self.failIf(self.policy.checkPermission('View', r_item, context))
        o_context = SecurityContext(self.uf.getUserById('joe'))
        # Push an executable with proxy roles on the stack
        eo = OwnedSetuidMethod().__of__(r_item)
        eo._proxy_roles = eo_roles
        context.stack.append(eo)
        self.failUnless(self.policy.checkPermission('View', r_item, context))

    def test_checkPermission_proxy_roles_limit_access(self):
        r_item = self.a.r_item
        context = self.context
        self.failUnless(self.policy.checkPermission('Foo', r_item, context))
        o_context = SecurityContext(self.uf.getUserById('joe'))
        # Push an executable with proxy roles on the stack
        eo = OwnedSetuidMethod().__of__(r_item)
        eo._proxy_roles = sysadmin_roles
        context.stack.append(eo)
        self.failIf(self.policy.checkPermission('Foo', r_item, context))

    def test_checkPermission_proxy_role_scope(self):
        self.a.subobject = ImplictAcqObject()
        subobject = self.a.subobject
        subobject.acl_users = UserFolder()
        subobject.acl_users._addUser('theowner', 'password', 'password', 
                                      eo_roles + sysadmin_roles, ())
        subobject.r_item = RestrictedSimpleItem()
        r_subitem = subobject.r_item
        r_subitem.owned_setuid_m = OwnedSetuidMethod()
        r_subitem.getPhysicalRoot = lambda root=self.a: root

        r_item = self.a.r_item
        r_item.getPhysicalRoot = lambda root=self.a: root
        context = self.context
        context.stack.append(r_subitem.owned_setuid_m.__of__(r_subitem))

        # Out of owner context
        self.failIf(self.policy.checkPermission('View', r_item, context))
        self.failIf(self.policy.checkPermission('Kill', r_item, context))

        # Inside owner context
        self.failIf(self.policy.checkPermission('View', r_subitem, context))
        self.failUnless(self.policy.checkPermission('Kill', r_subitem, context))

    def testUnicodeRolesForPermission(self):
        r_item = self.a.r_item
        context = self.context
        v = self.policy.checkPermission(u'View', r_item, context)
        self.assert_(not v, '_View_Permission should deny access to user')
        o_context = SecurityContext(self.uf.getUserById('theowner'))
        v = self.policy.checkPermission(u'View', r_item, o_context)
        self.assert_(v, '_View_Permission should grant access to theowner')

    def testAqNames(self):
        policy = self.policy
        names = {
            'aq_self': 0, 'aq_base': 0,
            'aq_parent': 1, 'aq_explicit': 1, 'aq_inner': 1
            }
        for name, allowed in names.items():
            if not allowed:
                self.assertRaises(Unauthorized, policy.validate,
                                  '', '', name, '', None)
            else:
                policy.validate('', '', name, '', None)

    def testProxyRoleScope(self):
        self.a.subobject = ImplictAcqObject()
        subobject = self.a.subobject
        subobject.acl_users = UserFolder()
        subobject.acl_users._addUser('theowner', 'password', 'password', 
                                      eo_roles + sysadmin_roles, ())
        subobject.item = UnprotectedSimpleItem()
        subitem = subobject.item
        subitem.owned_setuid_m = OwnedSetuidMethod()
        subitem.getPhysicalRoot = lambda root=self.a: root
        
        item = self.a.item
        item.getPhysicalRoot = lambda root=self.a: root
        self.context.stack.append(subitem.owned_setuid_m.__of__(subitem))
        
        # Out of owner context
        self.assertPolicyAllows(item, 'public_m')
        self.assertPolicyDenies(item, 'protected_m')
        self.assertPolicyDenies(item, 'owned_m')
        self.assertPolicyAllows(item, 'setuid_m')
        self.assertPolicyDenies(item, 'dangerous_m')

        # Inside owner context
        self.assertPolicyAllows(subitem, 'public_m')
        self.assertPolicyDenies(subitem, 'protected_m')
        self.assertPolicyDenies(subitem, 'owned_m')
        self.assertPolicyAllows(subitem, 'setuid_m')
        self.assertPolicyAllows(subitem, 'dangerous_m')

    def testUnicodeName(self):
        policy = self.policy
        assert policy.validate('', '', u'foo', '', None)

    if 0:
        # This test purposely generates a log entry.
        # Enable it if you don't mind it adding to the log.
        def testInsaneRoles(self):
            # Makes sure the policy doesn't blow up on bad input.
            c = SimpleClass()
            m = PublicMethod()
            c.m = m
            # Test good roles
            self.assertPolicyAllows(c, 'm')
            # Test bad roles
            m.__roles__ = 1950
            try:
                self.assertPolicyAllows(c, 'm')
            except TypeError:
                pass
            else:
                self.fail('Policy accepted bad __roles__')


class ISecurityPolicyConformance:

    def test_conforms_to_ISecurityPolicy(self):
        from AccessControl.interfaces import ISecurityPolicy
        from zope.interface.verify import verifyClass
        verifyClass(ISecurityPolicy, self._getTargetClass())

class Python_ZSPTests(ZopeSecurityPolicyTestBase,
                      ISecurityPolicyConformance,
                     ):
    def _getTargetClass(self):
        from AccessControl.ImplPython import ZopeSecurityPolicy
        return ZopeSecurityPolicy

class C_ZSPTests(ZopeSecurityPolicyTestBase,
                 ISecurityPolicyConformance,
                ):
    def _getTargetClass(self):
        from AccessControl.ImplC import ZopeSecurityPolicy
        return ZopeSecurityPolicy

def test_getRoles():
    """

    >>> from AccessControl.ZopeSecurityPolicy import getRoles
    
    >>> class C:
    ...     x = 'CRole'

    >>> class V:
    ...     x = 'VRole'

    >>> c = C()
    >>> c.v = V()

    >>> getRoles(c, None, c.v, 42)
    42
    >>> getRoles(c, 'inabox', c.v, 42)
    42

    >>> c.v.__roles__ = ['spam', 'eggs']

    >>> getRoles(c, None, c.v, 42)
    ['spam', 'eggs']

    >>> getRoles(c, 'withafox', c.v, 42)
    ['spam', 'eggs']

    >>> del c.v.__roles__

    >>> V.__roles__ = ('Manager', )

    >>> getRoles(c, None, c.v, 42)
    ('Manager',)
    >>> getRoles(c, 'withafox', c.v, 42)
    ('Manager',)

    >>> del V.__roles__

    >>> c.foo__roles__ = ('Foo', )

    >>> getRoles(c, None, c.v, 42)
    42
    >>> getRoles(c, 'foo', c.v, 42)
    42

    >>> C.foo__roles__ = ('Editor', )

    >>> getRoles(c, None, c.v, 42)
    42
    >>> getRoles(c, 'foo', c.v, 42)
    ('Editor',)

    >>> del C.foo__roles__

    >>> class ComputedRoles:
    ...     def __init__(self, roles):
    ...         self.roles = roles
    ...     def rolesForPermissionOn(self, ob):
    ...         return [ob.x] + self.roles

    >>> c.v.__roles__ = ComputedRoles(['Member'])
    >>> getRoles(c, None, c.v, 42)
    ['VRole', 'Member']
    >>> getRoles(c, 'foo', c.v, 42)
    ['VRole', 'Member']

    >>> c.foo__roles__ =  ComputedRoles(['Admin'])
    >>> getRoles(c, None, c.v, 42)
    ['VRole', 'Member']
    >>> getRoles(c, 'foo', c.v, 42)
    ['VRole', 'Member']

    >>> del c.v.__roles__
    >>> getRoles(c, None, c.v, 42)
    42
    >>> getRoles(c, 'foo', c.v, 42)
    42

    >>> C.foo__roles__ =  ComputedRoles(['Guest'])
    >>> getRoles(c, None, c.v, 42)
    42
    >>> getRoles(c, 'foo', c.v, 42)
    ['CRole', 'Guest']

    >>> V.__roles__ = ComputedRoles(['Member'])
    >>> getRoles(c, None, c.v, 42)
    ['VRole', 'Member']
    >>> getRoles(c, 'foo', c.v, 42)
    ['VRole', 'Member']
    """


def test_zsp_gets_right_roles_for_methods():
    """
    >>> from AccessControl.ZopeSecurityPolicy import ZopeSecurityPolicy
    >>> zsp = ZopeSecurityPolicy()
    >>> from ExtensionClass import Base
    >>> class C(Base):
    ...     def foo(self):
    ...         pass
    ...     foo__roles__ = ['greeneggs', 'ham']
    ...     def bar(self):
    ...         pass

    >>> class User:
    ...     def __init__(self, roles):
    ...         self.roles = roles
    ...     def allowed(self, value, roles):
    ...         for role in roles:
    ...             if role in self.roles:
    ...                 return True
    ...         return False

    >>> class Context:
    ...     stack = ()
    ...     def __init__(self, user):
    ...         self.user = user

    >>> c = C()
    
    >>> bool(zsp.validate(c, c, 'foo', c.foo, Context(User(['greeneggs']))))
    True
    
    >>> zsp.validate(c, c, 'foo', c.foo, Context(User(['spam'])))
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'foo' in this context

    >>> c.__roles__ = ['spam']
    >>> zsp.validate(c, c, 'foo', c.foo, Context(User(['spam'])))
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'foo' in this context

    >>> zsp.validate(c, c, 'bar', c.bar, Context(User(['spam'])))
    Traceback (most recent call last):
    ...
    Unauthorized: You are not allowed to access 'bar' in this context

    >>> c.__allow_access_to_unprotected_subobjects__ = 1
    >>> bool(zsp.validate(c, c, 'bar', c.bar, Context(User(['spam']))))
    True
    
    """

from doctest import DocTestSuite


class GetRolesWithMultiThreadTest(unittest.TestCase):

    def setUp(self):
        self._original_check_interval = sys.getcheckinterval()
        sys.setcheckinterval(1)

    def tearDown(self):
        sys.setcheckinterval(self._original_check_interval)

    def testGetRolesWithMultiThread(self):
        from AccessControl.ZopeSecurityPolicy import getRoles

        class C(object):
            pass

        class V1(object):
            class __roles__(object):
                @staticmethod
                def rolesForPermissionOn(ob):
                    return ['Member']

        class V2(object):
            class __roles__(object):
                @staticmethod
                def rolesForPermissionOn(ob):
                    return ['User']

        c = C()
        c.v1 = V1()
        c.v2 = V2()

        self.assertEqual(getRoles(c, None, c.v1, 42), ['Member'])
        self.assertEqual(getRoles(c, None, c.v2, 42), ['User'])
        mark = []

        def loop():
            while 1:
                getRoles(c, None, c.v2, 42)
                if len(mark) > 0:
                    return
        thread.start_new_thread(loop, ())
        try:
            for i in range(1000):
                self.assertEqual(getRoles(c, None, c.v1, 42), ['Member'])
        finally:
            mark.append(None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Python_ZSPTests, 'test'))
    suite.addTest(unittest.makeSuite(C_ZSPTests, 'test'))
    suite.addTest(DocTestSuite())
    suite.addTest(unittest.makeSuite(GetRolesWithMultiThreadTest))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
