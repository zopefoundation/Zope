##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Support for using zope.testbrowser from Zope2.
"""

import codecs

import transaction
from Testing.ZopeTestCase.functional import savestate
from Testing.ZopeTestCase.sandbox import AppZapper
from Testing.ZopeTestCase.zopedoctest.functional import auth_header
from zope.testbrowser import browser
from ZPublisher.httpexceptions import HTTPExceptionHandler
from ZPublisher.WSGIPublisher import publish_module


class WSGITestApp:

    def __init__(self, browser):
        self.browser = browser

    @savestate
    def __call__(self, environ, start_response):
        # This is similar to
        # Testing.ZopeTestCase.zopedoctest.functional.http

        # Commit previously done work
        transaction.commit()

        # Base64 encode auth header
        http_auth = 'HTTP_AUTHORIZATION'
        if http_auth in environ:
            environ[http_auth] = auth_header(environ[http_auth])

        publish = publish_module
        if self.browser.handleErrors:
            publish = HTTPExceptionHandler(publish)
        wsgi_result = publish(environ, start_response)

        # Sync transaction
        AppZapper().app()._p_jar.sync()

        return wsgi_result


class Browser(browser.Browser):
    """A Zope ``testbrowser` Browser that uses the Zope Publisher."""

    handleErrors = True
    raiseHttpErrors = True

    def __init__(self, url=None, wsgi_app=None):
        if wsgi_app is None:
            wsgi_app = WSGITestApp(self)
        super().__init__(url=url, wsgi_app=wsgi_app)

    def login(self, username, password):
        """Set up a correct HTTP Basic Auth Authorization header"""
        if not isinstance(username, bytes):
            username = username.encode('UTF-8')
        if not isinstance(password, bytes):
            password = password.encode('UTF-8')
        hdr = codecs.encode(b'%s:%s' % (username, password), 'base64')
        self.addHeader('Authorization', f'basic {hdr.decode("UTF-8")}')
