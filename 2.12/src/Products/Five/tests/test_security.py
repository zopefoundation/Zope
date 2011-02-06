##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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
"""Test security induced by ZCML

$Id$
"""

from zope.interface import implements
from zope.interface import Interface
from zope.schema import TextLine
from AccessControl.SecurityInfo import ClassSecurityInfo

class ISuperDummy(Interface):
    """
    """

    def superMethod():
        """
        """

class IDummy(ISuperDummy):
    """Just a marker interface"""

    def foo():
        """
        """

class Dummy1:
    implements(IDummy)
    def foo(self): pass
    def bar(self): pass
    def baz(self): pass
    def keg(self): pass
    def wot(self): pass
    def superMethod(self): pass

class Dummy2(Dummy1):
    security = ClassSecurityInfo()
    security.declarePublic('foo')
    security.declareProtected('View management screens', 'bar')
    security.declarePrivate('baz')
    security.declareProtected('View management screens', 'keg')

class IDummy3(Interface):
    attr = TextLine(title=u"Attribute")

class Dummy3:
    implements(IDummy3)
    attr = None

class Dummy4:
    foo = None

def test_security_equivalence():
    """This test demonstrates that the traditional declarative security of
    Zope 2 can be replaced by ZCML statements without any loss of
    information.

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()

    We start out with two classes, ``Dummy1`` and ``Dummy2``.  They
    are identical in every way, except that ``Dummy2`` has security
    declarations and ``Dummy1`` does not.  Before we do anything, none
    of them have security access controls:

      >>> from Products.Five.tests.test_security import Dummy1, Dummy2
      >>> hasattr(Dummy1, '__ac_permissions__')
      False
      >>> hasattr(Dummy2, '__ac_permissions__')
      False

    Before we can make security declarations through ZCML, we need to
    register the directive and the permission:

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('permissions.zcml', Products.Five)

    Now we initialize the security for ``Dummy2`` and provide some
    ZCML declarations for ``Dummy1``:

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope">
      ...   <class class="Products.Five.tests.test_security.Dummy1">
      ...     <allow attributes="foo" />
      ...     <!--deny attributes="baz" /--> <!-- XXX not yet supported -->
      ...   </class>
      ...   <class class="Products.Five.tests.test_security.Dummy1">
      ...     <require attributes="bar keg"
      ...              permission="zope2.ViewManagementScreens"
      ...              />
      ...   </class>
      ... </configure>
      ... '''
      >>> zcml.load_string(configure_zcml)

      >>> from App.class_init import InitializeClass
      >>> InitializeClass(Dummy2)

    Now we compare their access controls:

      >>> ac1 = getattr(Dummy1, '__ac_permissions__')
      >>> ac2 = getattr(Dummy2, '__ac_permissions__')
      >>> ac1 == ac2
      True

    Now we look at the individual permissions:

      >>> from AccessControl.ZopeSecurityPolicy import getRoles
      >>> from AccessControl import ACCESS_PUBLIC
      >>> from AccessControl import ACCESS_PRIVATE

      >>> dummy1 = Dummy1()
      >>> getRoles(dummy1, 'bar', dummy1.bar, ('Def',))
      ('Manager',)

      >>> getRoles(dummy1, 'keg', dummy1.keg, ('Def',))
      ('Manager',)

      >>> getRoles(dummy1, 'foo', dummy1.foo, ('Def',)) is ACCESS_PUBLIC
      True

      #>>> getRoles(dummy1, 'baz', dummy1.baz, ('Def',)) is ACCESS_PRIVATE
      #True XXX Not yet supported.

      >>> dummy2 = Dummy2()
      >>> getRoles(dummy2, 'bar', dummy2.bar, ('Def',))
      ('Manager',)

      >>> getRoles(dummy2, 'keg', dummy2.keg, ('Def',))
      ('Manager',)

      >>> getRoles(dummy2, 'foo', dummy2.foo, ('Def',)) is ACCESS_PUBLIC
      True

      >>> getRoles(dummy2, 'baz', dummy2.baz, ('Def',)) is ACCESS_PRIVATE
      True

    Before we end we should clean up after ourselves:

      >>> from Products.Five.security import clearSecurityInfo
      >>> clearSecurityInfo(Dummy1)
      >>> clearSecurityInfo(Dummy2)

      >>> tearDown()
    """

def test_allowed_interface():
    """This test demonstrates that allowed_interface security declarations work
    as expected.

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()

    Before we can make security declarations through ZCML, we need to
    register the directive and the permission:

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> import Products.Five.browser
      >>> zcml.load_config('meta.zcml', Products.Five.browser)
      >>> zcml.load_config('permissions.zcml', Products.Five)

    Now we provide some ZCML declarations for ``Dummy1``:

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            xmlns:browser="http://namespaces.zope.org/browser">
      ...   <browser:page
      ...       for="*"
      ...       name="testview"
      ...       permission="zope2.ViewManagementScreens"
      ...       class="Products.Five.tests.test_security.Dummy1"
      ...       allowed_interface="Products.Five.tests.test_security.IDummy" />
      ... </configure>
      ... '''
      >>> zcml.load_string(configure_zcml)

    We are going to check that roles are correctly setup, so we need getRoles.

      >>> from AccessControl.ZopeSecurityPolicy import getRoles
      >>> from AccessControl import ACCESS_PRIVATE

    Due to the nasty voodoo involved in Five's handling of view classes,
    browser:page doesn't apply security to Dummy1, but rather to the "magic"
    view class that is created at ZCML parse time.  That means we can't just
    instanciate with Dummy1() directly and expect a security-aware instance :(.
    Instead, we'll have to actually lookup the view.  The view was declared for
    "*", so we just use an instance of Dummy1 ;-).

    Instanciate a Dummy1 object to test with.

      >>> from Products.Five.tests.test_security import Dummy1
      >>> dummy1 = Dummy1()
      >>> from zope.component import getMultiAdapter
      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> view = getMultiAdapter((dummy1, request), name="testview")

    As 'foo' is defined in IDummy, it should have the 'Manager' role.

      >>> getRoles(view, 'foo', view.foo, ('Def',))
      ('Manager',)

    As 'wot' is not defined in IDummy, it should be private.

      >>> getRoles(view, 'wot', view.wot, ('Def',)) is ACCESS_PRIVATE
      True

    But 'superMethod' is defined on IDummy by inheritance from ISuperDummy, and
    so should have the 'Manager' role setup.

      >>> getRoles(view, 'superMethod', view.superMethod, ('Def',))
      ('Manager',)

      >>> tearDown()
    """

def test_set_warnings():
    """This test demonstrates that set_attributes and set_schema will result
    in warnings, not errors. This type of protection doesn't make sense in
    Zope 2, but we want to be able to re-use pure Zope 3 packages that use
    them without error.

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()

    Before we can make security declarations through ZCML, we need to
    register the directive and the permission:

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('permissions.zcml', Products.Five)

    Now we provide some ZCML declarations for ``Dummy1``:

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope">
      ...
      ...   <class class="Products.Five.tests.test_security.Dummy3">
      ...       <require
      ...           permission="zope2.View"
      ...           interface="Products.Five.tests.test_security.IDummy3"
      ...           />
      ...       <require
      ...           permission="cmf.ModifyPortalContent"
      ...           set_schema="Products.Five.tests.test_security.IDummy3"
      ...           />
      ...   </class>
      ...
      ...   <class class="Products.Five.tests.test_security.Dummy4">
      ...       <require
      ...           permission="cmf.ModifyPortalContent"
      ...           set_attributes="foo"
      ...           />
      ...   </class>
      ...
      ... </configure>
      ... '''
      
      Running this should not throw an exception (but will print a warning to
      stderr)
      
      >>> from warnings import catch_warnings
      >>> warned = []
      >>> with catch_warnings(record=True) as trapped:
      ...      zcml.load_string(configure_zcml)
      ...      warned.extend(list(trapped))
      >>> len(warned)
      2
      >>> str(warned[0].message)
      'The set_schema option...'
      >>> str(warned[1].message)
      'The set_attribute option...'
      >>> tearDown()
    """

def test_checkPermission():
    """
    Test checkPermission

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()

    Zope 3 has a function zope.security.checkPermission which provides
    an easy way of checking whether the currently authenticated user
    has the permission to access an object.  The function delegates to
    the security policy's checkPermission() method.

    Five has the same function, Five.security.checkPermission, but in
    a Zope2-compatible implementation.  It too uses the currently
    active security policy of Zope 2 for the actual permission
    checking.

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('permissions.zcml', Products.Five)

    In the following we want to test Five's checkPermission function.
    We do that by taking the test's folder and asserting several
    standard permissions.  What we want to assure is that
    checkPermission translates the Zope 2 permissions correctly,
    especially the edge cases:

    a) zope2.Public (which should always be available to everyone)

      >>> from Products.Five.security import checkPermission
      >>> checkPermission('zope2.Public', self.folder)
      True

    b) zope2.Private (which should never available to anyone)

      >>> checkPermission('zope.Private', self.folder)
      False
      >>> checkPermission('zope2.Private', self.folder)
      False

    Any other standard Zope 2 permission will also resolve correctly:

      >>> checkPermission('zope2.AccessContentsInformation', self.folder)
      True

    Invalid permissions will obviously result in a negative response:

      >>> checkPermission('notapermission', self.folder)
      False


    In addition to using Five's ``checkPermission`` function directly,
    we also expect the same behaviour when we use Zope 3's
    zope.security.checkPermission function.  Code from within Zope 3
    will use that and therefore it should work transparently.  For
    that to work, a new Five "interaction" needs to be started (the
    old one from placelesssetup needs to be ended first):

      >>> from zope.security.management import endInteraction
      >>> endInteraction()

      >>> from Products.Five.security import newInteraction
      >>> newInteraction()

    a) zope2.Public (which should always be available to everyone)

      >>> from zope.security import checkPermission
      >>> checkPermission('zope2.Public', self.folder)
      True

    b) zope2.Private (which should never available to anyone)

      >>> checkPermission('zope.Private', self.folder)
      False
      >>> checkPermission('zope2.Private', self.folder)
      False

    Any other standard Zope 2 permission will also resolve correctly:

      >>> checkPermission('zope2.AccessContentsInformation', self.folder)
      True

    Invalid permissions will obviously result in a negative response:

      >>> checkPermission('notapermission', self.folder)
      False


    Clean up:

      >>> tearDown()
    """

def test_register_permission():
    """This test demonstrates that if the <permission /> directive is used
    to create a permission that does not already exist, it is created on 
    startup, with roles defaulting to Manager.

      >>> from Testing.ZopeTestCase.placeless import setUp, tearDown
      >>> setUp()

    First, we need to configure the relevant parts of Five.

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('permissions.zcml', Products.Five)

    We can now register a permission in ZCML:

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            i18n_domain="fivetest">
      ...
      ...   <permission
      ...       id="Products.Five.tests.DummyPermission"
      ...       title="Five: Dummy permission"
      ...       />
      ...
      ... </configure>
      ... '''
      >>> zcml.load_string(configure_zcml)
      
    The permission will be made available globally, with default role set
    of ('Manager',).
      
      >>> roles = self.app.rolesOfPermission('Five: Dummy permission')
      >>> sorted(r['name'] for r in roles if r['selected'])
      ['Manager']

    Let's also ensure that permissions are not overwritten if they exist
    already:
      
      >>> from AccessControl.Permission import _registeredPermissions
      >>> import Products
      >>> _registeredPermissions['Five: Other dummy'] = 1
      >>> Products.__ac_permissions__ += (('Five: Other dummy', (), (),),)
      >>> self.app.manage_permission('Five: Other dummy', roles=['Anonymous'])

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            i18n_domain="fivetest">
      ...
      ...   <permission
      ...       id="Products.Five.tests.OtherDummy"
      ...       title="Five: Other dummy"
      ...       />
      ...
      ... </configure>
      ... '''
      >>> zcml.load_string(configure_zcml)

      >>> roles = self.app.rolesOfPermission('Five: Other dummy')
      >>> sorted(r['name'] for r in roles if r['selected'])
      ['Anonymous']

      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
