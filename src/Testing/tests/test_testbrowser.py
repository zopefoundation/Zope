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
"""Tests for the testbrowser module.
"""

import unittest
from urllib.error import HTTPError

import transaction
from AccessControl.Permissions import view
from OFS.SimpleItem import Item
from Testing.testbrowser import Browser
from Testing.ZopeTestCase import FunctionalTestCase
from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
from zExceptions import NotFound
from ZPublisher.httpexceptions import HTTPExceptionHandler
from ZPublisher.WSGIPublisher import publish_module


class CookieStub(Item):
    """This is a cookie stub."""

    def __call__(self, REQUEST):
        REQUEST.RESPONSE.setCookie('evil', 'cookie')
        return 'Stub'


class ExceptionStub(Item):
    """This is a stub, raising an exception."""

    def __call__(self, REQUEST):
        raise ValueError('dummy')


class RedirectStub(Item):
    """This is a stub, causing a redirect."""

    def __call__(self, REQUEST):
        return REQUEST.RESPONSE.redirect('/redirected')


class TestTestbrowser(FunctionalTestCase):

    def test_auth(self):
        # Based on Testing.ZopeTestCase.testFunctional
        basic_auth = f'{user_name}:{user_password}'
        self.folder.addDTMLDocument('secret_html', file='secret')
        self.folder.secret_html.manage_permission(view, ['Owner'])
        path = '/' + self.folder.absolute_url(1) + '/secret_html'

        # Test direct publishing
        response = self.publish(path + '/secret_html')
        self.assertEqual(response.getStatus(), 401)
        response = self.publish(path + '/secret_html', basic_auth)
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response.getBody(), b'secret')

        # Test browser
        url = 'http://localhost' + path
        browser = Browser()
        browser.raiseHttpErrors = False
        browser.open(url)
        self.assertTrue(browser.headers['status'].startswith('401'))

        browser.login(user_name, user_password)
        browser.open(url)
        self.assertTrue(browser.headers['status'].startswith('200'))
        self.assertEqual(browser.contents, 'secret')

    def test_cookies(self):
        # We want to make sure that our testbrowser correctly
        # understands cookies.
        self.folder._setObject('stub', CookieStub())

        # Test direct publishing
        response = self.publish('/test_folder_1_/stub')
        self.assertEqual(response.getCookie('evil')['value'], 'cookie')

        browser = Browser()
        browser.open('http://localhost/test_folder_1_/stub')
        self.assertEqual(browser.cookies.get('evil'), 'cookie')

    def test_handle_errors_true(self):
        self.folder._setObject('stub', ExceptionStub())
        browser = Browser()

        # An error which cannot be handled by Zope is propagated to the client:
        with self.assertRaises(ValueError):
            browser.open('http://localhost/test_folder_1_/stub')
        self.assertIsNone(browser.contents)

        # Handled errors become an instance of `HTTPError`:
        with self.assertRaises(HTTPError):
            browser.open('http://localhost/nothing-is-here')
        self.assertTrue(browser.headers['status'].startswith('404'))

    def test_handle_errors_true_redirect(self):
        self.folder._setObject('redirect', RedirectStub())
        browser = Browser()

        with self.assertRaises(HTTPError):
            browser.open('http://localhost/test_folder_1_/redirect')
        self.assertTrue(browser.headers['status'].startswith('404'))
        self.assertEqual(browser.url, 'http://localhost/redirected')

    def test_handle_errors_false(self):
        self.folder._setObject('stub', ExceptionStub())
        browser = Browser()
        browser.handleErrors = False

        # Even errors which can be handled by Zope go to the client:
        with self.assertRaises(NotFound):
            browser.open('http://localhost/nothing-is-here')
        self.assertTrue(browser.contents is None)

    def test_handle_errors_false_redirect(self):
        self.folder._setObject('redirect', RedirectStub())
        browser = Browser()
        browser.handleErrors = False

        with self.assertRaises(NotFound):
            browser.open('http://localhost/test_folder_1_/redirect')
        self.assertTrue(browser.contents is None)

    def test_handle_errors_false_HTTPExceptionHandler_in_app(self):
        """HTTPExceptionHandler does not handle errors if requested via WSGI.

        This is needed when HTTPExceptionHandler is part of the WSGI pipeline.
        """
        class WSGITestAppWithHTTPExceptionHandler:
            """Minimized testbrowser.WSGITestApp with HTTPExceptionHandler."""

            def __call__(self, environ, start_response):
                publish = HTTPExceptionHandler(publish_module)
                wsgi_result = publish(environ, start_response)

                return wsgi_result

        self.folder._setObject('stub', ExceptionStub())
        transaction.commit()
        browser = Browser(wsgi_app=WSGITestAppWithHTTPExceptionHandler())
        browser.handleErrors = False

        with self.assertRaises(ValueError):
            browser.open('http://localhost/test_folder_1_/stub')
        self.assertIsNone(browser.contents)

    def test_raise_http_errors_false(self):
        self.folder._setObject('stub', ExceptionStub())
        browser = Browser()
        browser.raiseHttpErrors = False

        # Internal server errors are still raised:
        with self.assertRaises(ValueError):
            browser.open('http://localhost/test_folder_1_/stub')
        self.assertIsNone(browser.contents)

        # But errors handled by Zope do not create an exception:
        browser.open('http://localhost/nothing-is-here')
        self.assertTrue(browser.headers['status'].startswith('404'))

    def test_raise_http_errors_false_redirect(self):
        self.folder._setObject('redirect', RedirectStub())
        browser = Browser()
        browser.raiseHttpErrors = False

        browser.open('http://localhost/test_folder_1_/redirect')
        self.assertTrue(browser.headers['status'].startswith('404'))
        self.assertEqual(browser.url, 'http://localhost/redirected')

    def test_headers_camel_case(self):
        # The Zope2 response mungs headers so they come out
        # in camel case. We should do the same.
        self.folder._setObject('stub', CookieStub())

        browser = Browser()
        browser.open('http://localhost/test_folder_1_/stub')
        header_text = str(browser.headers)
        self.assertTrue('Content-Length: ' in header_text)
        self.assertTrue('Content-Type: ' in header_text)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestTestbrowser)
