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
    >>> from zope.interface import implements
    >>> from zope.component import queryMultiAdapter
    >>> class Unwrapped:
    ...     implements(sc.ISimpleContent)
    >>> unwrapped = Unwrapped()

    Simple views should work fine without having their contexts wrapped:

    >>> eagle = queryMultiAdapter((unwrapped, self.app.REQUEST),
    ...                            Interface, 'eagle.txt')
    >>> eagle is not None
    True
    >>> from Products.Five.browser.tests.pages import SimpleView
    >>> isinstance(eagle, SimpleView)
    True
    >>> eagle()
    u'The eagle has landed'

    We also want to be able to render the file-based ZPT without requiring
    that the context be wrapped:

    >>> falcon = queryMultiAdapter((unwrapped, self.app.REQUEST),
    ...                            Interface, 'falcon.html')
    >>> falcon is not None
    True
    >>> from Products.Five.browser.tests.pages import SimpleView
    >>> isinstance(falcon, SimpleView)
    True
    >>> print falcon()
    <p>The falcon has taken flight</p>

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
        FunctionalDocFileSuite('aqlegacy_ftest.txt',
                               package='Products.Five.browser.tests'),
        ))
