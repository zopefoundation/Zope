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
"""Unit tests for marker interface views.
"""

def test_editview():
    """
    Set everything up:

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()
      >>> import AccessControl
      >>> import Products.Five
      >>> import Products.Five.utilities
      >>> from Zope2.App import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('permissions.zcml', AccessControl)
      >>> zcml.load_config('configure.zcml', Products.Five.utilities)
      >>> from Products.Five.utilities.browser.marker import EditView
      >>> from Products.Five.tests.testing.simplecontent import SimpleContent
      >>> obj = SimpleContent('foo', 'Foo').__of__(self.folder)

    Create an EditView:

      >>> view = EditView(obj, {})
      >>> view.context.aq_inner is obj
      True
      >>> view.request
      {}
      >>> view.getAvailableInterfaceNames()
      []
      >>> view.getDirectlyProvidedNames()
      []
      >>> view.getInterfaceNames()
      [...ISimpleContent...]

    Try to add a marker interface that doesn't exist:

      >>> view.update(('__main__.IFooMarker',), ())
      Traceback (most recent call last):
      ...
      ComponentLookupError...

    Now create the marker interface:

      >>> from Products.Five.tests.testing.simplecontent import ISimpleContent
      >>> class IFooMarker(ISimpleContent): pass
      >>> from zope.component.interface import provideInterface
      >>> provideInterface('', IFooMarker)
      >>> view.getAvailableInterfaceNames()
      [...IFooMarker...]
      >>> view.getDirectlyProvidedNames()
      []

    And try again to add it to the object:

      >>> view.update(('__main__.IFooMarker',), ())
      >>> view.getAvailableInterfaceNames()
      []
      >>> view.getDirectlyProvidedNames()
      [...IFooMarker...]

    And remove it again:

      >>> view.update((), ('__main__.IFooMarker',))
      >>> view.getAvailableInterfaceNames()
      [...IFooMarker...]
      >>> view.getDirectlyProvidedNames()
      []

    Finally tear down:

      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
