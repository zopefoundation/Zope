##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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

$Id: test_security.py 14595 2005-07-12 21:26:12Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from zope.interface import Interface, implements
from AccessControl import ClassSecurityInfo

class IDummy(Interface):
    """Just a marker interface"""

class Dummy1:
    implements(IDummy)
    def foo(self): pass
    def bar(self): pass
    def baz(self): pass
    def keg(self): pass
    def wot(self): pass

class Dummy2(Dummy1):
    security = ClassSecurityInfo()
    security.declarePublic('foo')
    security.declareProtected('View management screens', 'bar')
    security.declarePrivate('baz')
    security.declareProtected('View management screens', 'keg')

def test_security_equivalence():
    """This test demonstrates that the traditional declarative security of
    Zope 2 can be replaced by ZCML statements without any loss of
    information.

      >>> from zope.app.tests.placelesssetup import setUp, tearDown
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
      ...   <content class="Products.Five.tests.test_security.Dummy1">
      ...     <allow attributes="foo" />
      ...     <!--deny attributes="baz" /--> <!-- XXX not yet supported -->
      ...     <require attributes="bar keg"
      ...              permission="zope2.ViewManagementScreens"
      ...              />
      ...   </content>
      ... </configure>
      ... '''
      >>> zcml.load_string(configure_zcml)

      >>> from Globals import InitializeClass
      >>> InitializeClass(Dummy2)

    Now we compare their access controls:

      >>> ac1 = getattr(Dummy1, '__ac_permissions__')
      >>> ac2 = getattr(Dummy2, '__ac_permissions__')
      >>> ac1 == ac2
      True

    Now we look at the individual permissions:

      >>> bar_roles1 = getattr(Dummy1, 'bar__roles__').__of__(Dummy1)
      >>> bar_roles1.__of__(Dummy1)
      ('Manager',)

      >>> keg_roles1 = getattr(Dummy1, 'keg__roles__').__of__(Dummy1)
      >>> keg_roles1.__of__(Dummy1)
      ('Manager',)

      >>> foo_roles1 = getattr(Dummy1, 'foo__roles__')
      >>> foo_roles1 is None
      True

      >>> # XXX Not yet supported.
      >>> # baz_roles1 = getattr(Dummy1, 'baz__roles__')
      >>> # baz_roles1
      ()
        
      >>> bar_roles2 = getattr(Dummy2, 'bar__roles__').__of__(Dummy2)
      >>> bar_roles2.__of__(Dummy2)
      ('Manager',)

      >>> keg_roles2 = getattr(Dummy2, 'keg__roles__').__of__(Dummy2)
      >>> keg_roles2.__of__(Dummy2)
      ('Manager',)

      >>> foo_roles2 = getattr(Dummy2, 'foo__roles__')
      >>> foo_roles2 is None
      True

      >>> baz_roles2 = getattr(Dummy2, 'baz__roles__')
      >>> baz_roles2
      ()

    Before we end we should clean up after ourselves:

      >>> from Products.Five.security import clearSecurityInfo
      >>> clearSecurityInfo(Dummy1)
      >>> clearSecurityInfo(Dummy2)

      >>> tearDown()
    """

def test_checkPermission():
    """
    Test checkPermission

      >>> from zope.app.tests.placelesssetup import setUp, tearDown
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

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
