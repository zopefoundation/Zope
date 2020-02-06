##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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
"""Test HTTPServer module"""

import unittest
import urlparse


class FakeMedusaServer:

    def __init__(self):
        self.port = 80
        self.request_server_name = 'localhost'
        self.SERVER_IDENT = 'whoami?'
        self.logger = None


class FakeMedusaChannel:

    def __init__(self):
        self.server = FakeMedusaServer()
        self.creation_time = 'now'
        self.addr=('0.0.0.0', 7865)


class FakeMedusaRequest:

    def __init__(self):
        self.channel = FakeMedusaChannel()
        self.command = 'get'
        self.port = 80
        self.version = '0.9'
        self.header = []
        self.url = 'http://localhost/foo/bar?key1=val1'

    def split_uri(self):
        return urlparse.urlparse(self.url)[2:]


class zhttp_handlerTests(unittest.TestCase):
    """ Tests for ZServer.HTTPServer.zhttp_handler """

    def _getTargetClass(self):
        from ZServer.HTTPServer import zhttp_handler
        return zhttp_handler

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeRequest(self, **kw):
        req = FakeMedusaRequest()
        for key, value in kw.items():
            req.header.append('%s:%s' % (key, value))
        return req

    def test_header_spoofing(self):
        # See https://www.djangoproject.com/weblog/2015/jan/13/security/
        handler = self._makeOne('Zope2')

        req = self._makeRequest(**{'X-AUTH-USER': 'CORRECT'})
        env = handler.get_environment(req)
        self.assertIn('HTTP_X_AUTH_USER', env)
        self.assertEqual(env['HTTP_X_AUTH_USER'], 'CORRECT')

        req = self._makeRequest(**{'X_AUTH-USER': 'SPOOF'})
        env = handler.get_environment(req)
        self.assertNotIn('HTTP_X_AUTH_USER', env)

        req = self._makeRequest(**{'x_auth_user': 'SPOOF'})
        env = handler.get_environment(req)
        self.assertNotIn('HTTP_X_AUTH_USER', env)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTests((
        unittest.makeSuite(zhttp_handlerTests),
    ))
    return suite
