##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for AcceleratedCacheManager module.

$Id$
"""
import unittest
import threading
import time
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer

class PurgingHTTPRequestHandler(SimpleHTTPRequestHandler):

    protocol_version = 'HTTP/1.0'

    def do_PURGE(self):

        """Serve a PURGE request."""
        self.server.test_case.purged_host = self.headers.get('Host','xxx')
        self.server.test_case.purged_path = self.path
        self.send_response(200)
        self.end_headers()

    def log_request(self, code='ignored', size='ignored'):
        pass


class DummyObject:

    _PATH = '/path/to/object'

    def getPhysicalPath(self):
        return tuple(self._PATH.split('/'))

class AcceleratedHTTPCacheTests(unittest.TestCase):

    _SERVER_PORT = 1888
    thread = purged_host = purged_path = None

    def tearDown(self):
        if self.thread:
            self.httpd.server_close()
            self.thread.join(2)

    def _getTargetClass(self):

        from Products.StandardCacheManagers.AcceleratedHTTPCacheManager \
            import AcceleratedHTTPCache

        return AcceleratedHTTPCache

    def _makeOne(self, *args, **kw):

        return self._getTargetClass()(*args, **kw)

    def _handleServerRequest(self):

        server_address = ('', self._SERVER_PORT)

        self.httpd = HTTPServer(server_address, PurgingHTTPRequestHandler)
        self.httpd.test_case = self

        sa = self.httpd.socket.getsockname()
        self.thread = threading.Thread(target=self.httpd.handle_request)
        self.thread.setDaemon(True)
        self.thread.start()
        time.sleep(0.2) # Allow time for server startup

    def test_PURGE_passes_Host_header(self):

        _TO_NOTIFY = 'localhost:%d' % self._SERVER_PORT

        cache = self._makeOne()
        cache.notify_urls = ['http://%s' % _TO_NOTIFY]
        object = DummyObject()

        # Run the HTTP server for this test.
        self._handleServerRequest()

        cache.ZCache_invalidate(object)

        self.assertEqual(self.purged_host, _TO_NOTIFY)
        self.assertEqual(self.purged_path, DummyObject._PATH)

def test_suite():
    return unittest.makeSuite(AcceleratedHTTPCacheTests)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

