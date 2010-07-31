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
"""Unit tests for the testbrowser module.
"""

import unittest
from Testing.ZopeTestCase import FunctionalDocTestSuite
from OFS.SimpleItem import Item

class CookieStub(Item):
    """This is a cookie stub."""

    def __call__(self, REQUEST):
        REQUEST.RESPONSE.setCookie('evil', 'cookie')
        return 'Stub'

def doctest_cookies():
    """
    We want to make sure that our testbrowser correctly understands
    cookies.  We'll add a stub to ``self.folder`` that sets a cookie.

        >>> from Testing.tests.test_testbrowser import CookieStub
        >>> self.folder._setObject('stub', CookieStub())
        'stub'

    This response looks alright:

        >>> response = self.publish('/test_folder_1_/stub')
        >>> print str(response) #doctest: +ELLIPSIS
        Status: 200 OK
        ...
        Set-Cookie: evil="cookie"
        ...

    Let's try to look at the same folder with testbrowser:

        >>> from Testing.testbrowser import Browser
        >>> browser = Browser()
        >>> browser.open('http://localhost/test_folder_1_/stub')
        >>> 'Set-Cookie: evil="cookie"' in str(browser.headers)
        True
    """

def doctest_camel_case_headers():
    """Make sure that the headers come out in camel case.

    Some setup:

        >>> from Testing.tests.test_testbrowser import CookieStub
        >>> self.folder._setObject('stub', CookieStub())
        'stub'

    The Zope2 response mungs headers so they come out in camel case we should
    do the same. We will test a few:

        >>> from Testing.testbrowser import Browser
        >>> browser = Browser()
        >>> browser.open('http://localhost/test_folder_1_/stub')
        >>> 'Content-Length: ' in str(browser.headers)
        True
        >>> 'Content-Type: ' in str(browser.headers)
        True
    """


def test_suite():
    return unittest.TestSuite((
            FunctionalDocTestSuite(),
            ))
