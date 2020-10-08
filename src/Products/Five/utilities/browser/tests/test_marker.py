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
""" Tests for the marker interface edit views
"""
import AccessControl
import Products.Five
import Products.Five.utilities
from Products.Five.tests.testing.simplecontent import ISimpleContent
from Products.Five.tests.testing.simplecontent import SimpleContent
from Products.Five.utilities.browser.marker import EditView
from Testing.ZopeTestCase import ZopeTestCase
from Zope2.App import zcml
from zope.component import ComponentLookupError
from zope.component.interface import provideInterface
from zope.component.testing import setUp as component_setUp
from zope.component.testing import tearDown as component_tearDown


ISimpleContentName = 'Products.Five.tests.testing.simplecontent.ISimpleContent'
IFooMarkerName = 'Products.Five.utilities.browser.tests.test_marker.IFooMarker'


class IFooMarker(ISimpleContent):
    pass


class MarkerViewTests(ZopeTestCase):

    def setUp(self):
        super().setUp()
        component_setUp()
        zcml.load_config('meta.zcml', Products.Five)
        zcml.load_config('permissions.zcml', AccessControl)
        zcml.load_config('configure.zcml', Products.Five.utilities)

    def tearDown(self):
        super().tearDown()
        component_tearDown()

    def test_editview(self):
        obj = SimpleContent('foo', 'Foo').__of__(self.app.test_folder_1_)
        view = EditView(obj, {})

        # Test state before making any changes
        self.assertTrue(view.context.aq_inner is obj)
        self.assertEqual(view.request, {})
        self.assertEqual(view.getAvailableInterfaceNames(), [])
        self.assertEqual(view.getDirectlyProvidedNames(), [])
        self.assertIn({'name': ISimpleContentName}, view.getInterfaceNames())

        # Try to add a marker interface that doesn't exist
        self.assertRaises(ComponentLookupError, view.update,
                          ('__main__.IFooMarker',), ())

        # Now create the marker interface and try again
        provideInterface('', IFooMarker)
        self.assertIn({'name': IFooMarkerName},
                      view.getAvailableInterfaceNames())
        self.assertEqual(view.getDirectlyProvidedNames(), [])

        # And try again to add it to the object
        view.update((IFooMarkerName,), ())
        self.assertEqual(view.getAvailableInterfaceNames(), [])
        self.assertIn({'name': IFooMarkerName},
                      view.getDirectlyProvidedNames())

        # And remove it again
        view.update((), (IFooMarkerName,))
        self.assertIn({'name': IFooMarkerName},
                      view.getAvailableInterfaceNames())
        self.assertEqual(view.getDirectlyProvidedNames(), [])
