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
"""Test browser pages
"""
import unittest

import Products.Five.browser.tests
import Testing.ZopeTestCase
import zope.component.testing
from Products.Five.tests.testing.simplecontent import manage_addSimpleContent
from Testing.testbrowser import Browser
from Zope2.App import zcml
from zope.testbrowser.browser import HTTPError


def test_view_with_unwrapped_context():
    """
    It may be desirable when writing tests for views themselves to
    provide dummy contexts which are not wrapped.

    >>> import Products.Five.browser.tests
    >>> from Zope2.App import zcml
    >>> zcml.load_config("configure.zcml", Products.Five)
    >>> zcml.load_config('pages.zcml', package=Products.Five.browser.tests)
    >>> from Products.Five.tests.testing import simplecontent as sc
    >>> from zope.interface import Interface
    >>> from zope.interface import implementer
    >>> from zope.component import queryMultiAdapter
    >>> @implementer(sc.ISimpleContent)
    ... class Unwrapped(object):
    ...     pass
    >>> unwrapped = Unwrapped()

    Simple views should work fine without having their contexts wrapped:

    >>> eagle = queryMultiAdapter((unwrapped, self.app.REQUEST),  # NOQA: F821
    ...                            Interface, 'eagle.txt')
    >>> eagle is not None
    True
    >>> from Products.Five.browser.tests.pages import SimpleView
    >>> isinstance(eagle, SimpleView)
    True
    >>> eagle() == 'The eagle has landed'
    True

    We also want to be able to render the file-based ZPT without requiring
    that the context be wrapped:

    >>> falcon = queryMultiAdapter((unwrapped, self.app.REQUEST),  # NOQA: F821
    ...                            Interface, 'falcon.html')
    >>> falcon is not None
    True
    >>> from Products.Five.browser.tests.pages import SimpleView
    >>> isinstance(falcon, SimpleView)
    True
    >>> print(falcon())
    <p>The falcon has taken flight</p>

    Clean up:

    >>> from zope.component.testing import tearDown
    >>> tearDown()
    """


class TestPublishTraverse(Testing.ZopeTestCase.FunctionalTestCase):

    def setUp(self):
        super().setUp()
        zcml.load_config("configure.zcml", Products.Five)
        zcml.load_config('pages.zcml', package=Products.Five.browser.tests)
        uf = self.app.acl_users
        uf.userFolderAddUser('manager', 'manager_pass', ['Manager'], [])
        manage_addSimpleContent(self.folder, 'testoid', 'x')
        self.browser = Browser()
        self.browser.login('manager', 'manager_pass')

    def tearDown(self):
        zope.component.testing.tearDown()
        super().tearDown()

    def test_publishTraverse_to_allowed_name(self):
        # The ``eagle.method`` view has a method ``eagle`` that is registered
        # with ``allowed_attributes`` in pages.zcml. This attribute should be
        # reachable through ``publishTraverse`` on the view.

        folder = self.folder
        view = folder.unrestrictedTraverse('testoid/eagle.method')

        # Publishing traversal with the default adapter should work:

        from ZPublisher.BaseRequest import DefaultPublishTraverse
        request = folder.REQUEST
        adapter = DefaultPublishTraverse(view, request)
        result = adapter.publishTraverse(request, 'eagle')()
        self.assertIn('The eagle has landed', result)

        # Publishing via browser works, too:

        self.browser.open(
            'http://localhost/test_folder_1_/testoid/eagle.method/eagle')
        self.assertEqual('The eagle has landed', self.browser.contents)

    def test_publishTraverse_to_not_allowed_name(self):
        # The ``eagle.method`` view has a method ``mouse`` but it is not
        # registered with ``allowed_attributes`` in pages.zcml. This attribute
        # should be not be accessible. It leads to a HTTP-404, so we do not
        # tell the world about our internal methods:
        with self.assertRaises(HTTPError) as err:
            self.browser.open(
                'http://localhost/test_folder_1_/testoid/eagle.method/mouse')
        self.assertEqual('HTTP Error 404: Not Found', str(err.exception))

    def test_publishTraverse_to_allowed_interface(self):
        # The ``cheeseburger`` view has a method ``meat`` that is
        # registered via ``allowed_interface`` in pages.zcml. This attribute
        # should be reachable through ``publishTraverse`` on the view.

        folder = self.folder
        view = folder.unrestrictedTraverse('testoid/cheeseburger')

        # Publishing traversal with the default adapter should work:

        from ZPublisher.BaseRequest import DefaultPublishTraverse
        request = folder.REQUEST
        adapter = DefaultPublishTraverse(view, request)
        result = adapter.publishTraverse(request, 'meat')()
        self.assertIn('yummi', result)

        # Publishing via browser works, too:

        self.browser.open(
            'http://localhost/test_folder_1_/testoid/cheeseburger/meat')
        self.assertEqual('yummi', self.browser.contents)

    def test_publishTraverse_to_not_allowed_interface(self):
        # The ``cheeseburger`` view has a method ``cheese`` but it is not
        # registered via ``allowed_interface`` in pages.zcml. This attribute
        # should be not be accessible. It leads to a HTTP-404, so we do not
        # tell the world about our internal methods:
        with self.assertRaises(HTTPError) as err:
            self.browser.open(
                'http://localhost/test_folder_1_/testoid/cheeseburger/cheese')
        self.assertEqual('HTTP Error 404: Not Found', str(err.exception))


def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    from Testing.ZopeTestCase import ZopeDocFileSuite
    from Testing.ZopeTestCase import ZopeDocTestSuite

    return unittest.TestSuite((
        ZopeDocTestSuite(),
        unittest.defaultTestLoader.loadTestsFromTestCase(TestPublishTraverse),
        ZopeDocFileSuite('pages.txt', package='Products.Five.browser.tests'),
        FunctionalDocFileSuite('pages_ftest.txt',
                               package='Products.Five.browser.tests'),
    ))
