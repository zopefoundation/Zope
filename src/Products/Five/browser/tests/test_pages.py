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


def test_publishTraverse_to_allowed_name():
    """
    The ``eagle.method`` view has a method ``eagle`` that is registered
    with ``allowed_attributes`` in pages.zcml. This attribute should be
    reachable through ``publishTraverse`` on the view.

    >>> import Products.Five.browser.tests
    >>> from Zope2.App import zcml
    >>> zcml.load_config("configure.zcml", Products.Five)
    >>> zcml.load_config('pages.zcml', package=Products.Five.browser.tests)

    >>> from Products.Five.tests.testing.simplecontent import (
    ... manage_addSimpleContent)
    >>> manage_addSimpleContent(self.folder, 'testoid', 'Testoid')

    >>> view = folder.unrestrictedTraverse('testoid/eagle.method')
    >>> request = self.folder.REQUEST

    Publishing traversal with the default adapter should work:

    >>> from ZPublisher.BaseRequest import DefaultPublishTraverse
    >>> adapter = DefaultPublishTraverse(view, request)
    >>> adapter.publishTraverse(request, 'eagle')()
    'The eagle has landed'

    Publishing traversal should also work directly:

    >>> view.publishTraverse(request, 'eagle')()
    'The eagle has landed'

    Clean up:

    >>> from zope.component.testing import tearDown
    >>> tearDown()
    """


def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    from Testing.ZopeTestCase import ZopeDocFileSuite
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return unittest.TestSuite((
        ZopeDocTestSuite(),
        ZopeDocFileSuite('pages.txt', package='Products.Five.browser.tests'),
        FunctionalDocFileSuite('pages_ftest.txt',
                               package='Products.Five.browser.tests'),
    ))
