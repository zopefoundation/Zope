##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Tests of ZopeSecurityPolicy
"""

__rcs_id__='$Id: testZopeSecurityPolicy.py,v 1.2 2001/10/18 20:22:33 shane Exp $'
__version__='$Revision: 1.2 $'[11:-2]

import os, sys, unittest

import ZODB
try:
    from zExceptions import Unauthorized
except ImportError:
    Unauthorized = 'Unauthorized'
from AccessControl.ZopeSecurityPolicy import ZopeSecurityPolicy
from AccessControl.User import UserFolder
from AccessControl.SecurityManagement import SecurityContext
from Acquisition import Implicit, Explicit, aq_base
from MethodObject import Method
from ComputedAttribute import ComputedAttribute


user_roles = ('RoleOfUser',)
eo_roles = ('RoleOfExecutableOwner',)
sysadmin_roles = ('RoleOfSysAdmin',)


class App(Explicit):
    pass


class PublicMethod (Method):
    def getOwner(self):
        return None

    __roles__ = None


class ProtectedMethod (PublicMethod):
    __roles__ = user_roles


class OwnedMethod (PublicMethod):
    __roles__ = eo_roles

    def getOwner(self):
        return self.aq_parent.aq_parent.acl_users.getUserById('theowner')


class setuidMethod (PublicMethod):
    _proxy_roles = sysadmin_roles


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


class UnprotectedSimpleItem (SimpleItemish):

    __allow_access_to_unprotected_subobjects__ = 1


class RestrictedSimpleItem (SimpleItemish):

    __allow_access_to_unprotected_subobjects__ = 0

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


class ZopeSecurityPolicyTests (unittest.TestCase):

    policy = ZopeSecurityPolicy()

    def setUp(self):
        a = App()
        self.a = a
        a.item = UnprotectedSimpleItem()
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

    def assertPolicyAllows(self, ob, attrname):
        res = self.policy.validate(ob, ob, attrname, getattr(ob, attrname),
                                   self.context)
        if not res:
            assert 0, 'Policy quietly denied %s' % attrname

    def assertPolicyDenies(self, ob, attrname):
        try:
            res = self.policy.validate(ob, ob, attrname, getattr(ob, attrname),
                                       self.context)
        except Unauthorized:
            # Passed the test.
            pass
        else:
            if res:
                assert 0, 'Policy quietly allowed %s' % attrname
            else:
                assert 0, ('Policy denied %s, but did not '
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

    def testAccessToUnprotectedSubobjects(self):
        item = self.item
        r_item = self.a.r_item
        item1 = self.a.item1
        item2 = self.a.item2
        item3 = self.a.item3
        self.assertPolicyAllows(item,  'public_prop')
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

    def testRolesForPermission(self):
        # Test of policy.checkPermission().
        r_item = self.a.r_item
        context = self.context
        v = self.policy.checkPermission('View', r_item, context)
        assert not v, '_View_Permission should deny access to user'
        o_context = SecurityContext(self.uf.getUserById('theowner'))
        v = self.policy.checkPermission('View', r_item, o_context)
        assert v, '_View_Permission should grant access to theowner'
        
    def testAqNames(self):
        policy = self.policy
        assert not policy.validate('', '', 'aq_self', '', None)
        assert not policy.validate('', '', 'aq_base', '', None)
        assert policy.validate('', '', 'aq_parent', '', None)
        assert policy.validate('', '', 'aq_explicit', '', None)

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
                assert 0, 'Policy accepted bad __roles__'


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ZopeSecurityPolicyTests))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()

