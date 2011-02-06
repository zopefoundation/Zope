##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
""" Unit tests for AcceleratedCacheManager module.

$Id$
"""

import unittest
from Products.StandardCacheManagers.AcceleratedHTTPCacheManager \
     import AcceleratedHTTPCache, AcceleratedHTTPCacheManager


class DummyObject:

    def __init__(self, path='/path/to/object', urlpath=None):
        self.path = path
        if urlpath is None:
            self.urlpath = path
        else:
            self.urlpath = urlpath

    def getPhysicalPath(self):
        return tuple(self.path.split('/'))

    def absolute_url_path(self):
        return self.urlpath

class MockResponse:
    status = '200'
    reason = "who knows, I'm just a mock"

def MockConnectionClassFactory():
    # Returns both a class that mocks an HTTPConnection,
    # and a reference to a data structure where it logs requests.
    request_log = []

    class MockConnection:
        # Minimal replacement for httplib.HTTPConnection.
        def __init__(self, host):
            self.host = host
            self.request_log = request_log

        def request(self, method, path):
            self.request_log.append({'method':method,
                                     'host':self.host,
                                     'path':path,})
        def getresponse(self):
            return MockResponse()

    return MockConnection, request_log


class AcceleratedHTTPCacheTests(unittest.TestCase):

    def _getTargetClass(self):
        return AcceleratedHTTPCache

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_PURGE_passes_Host_header(self):
        _TO_NOTIFY = 'localhost:1888'
        cache = self._makeOne()
        cache.notify_urls = ['http://%s' % _TO_NOTIFY]
        cache.connection_factory, requests = MockConnectionClassFactory()
        dummy = DummyObject()
        cache.ZCache_invalidate(dummy)
        self.assertEqual(len(requests), 1)
        result = requests[-1]
        self.assertEqual(result['method'], 'PURGE')
        self.assertEqual(result['host'], _TO_NOTIFY)
        self.assertEqual(result['path'], dummy.path)

    def test_multiple_notify(self):
        cache = self._makeOne()
        cache.notify_urls = ['http://foo', 'bar', 'http://baz/bat']
        cache.connection_factory, requests = MockConnectionClassFactory()
        cache.ZCache_invalidate(DummyObject())
        self.assertEqual(len(requests), 3)
        self.assertEqual(requests[0]['host'], 'foo')
        self.assertEqual(requests[1]['host'], 'bar')
        self.assertEqual(requests[2]['host'], 'baz')
        cache.ZCache_invalidate(DummyObject())
        self.assertEqual(len(requests), 6)

    def test_vhost_purging_1447(self):
        # Test for http://www.zope.org/Collectors/Zope/1447
        cache = self._makeOne()
        cache.notify_urls = ['http://foo.com']
        cache.connection_factory, requests = MockConnectionClassFactory()
        dummy = DummyObject(urlpath='/published/elsewhere')
        cache.ZCache_invalidate(dummy)
        # That should fire off two invalidations,
        # one for the physical path and one for the abs. url path.
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[0]['path'], dummy.absolute_url_path())
        self.assertEqual(requests[1]['path'], dummy.path)


class CacheManagerTests(unittest.TestCase):

    def _getTargetClass(self):
        return AcceleratedHTTPCacheManager

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeContext(self):
        from OFS.Folder import Folder
        root = Folder()
        root.getPhysicalPath = lambda: ('', 'some_path',)
        cm_id = 'http_cache'
        manager = self._makeOne(cm_id)
        root._setObject(cm_id, manager)
        manager = root[cm_id]
        return root, manager

    def test_add(self):
        # ensure __init__ doesn't raise errors.
        root, cachemanager = self._makeContext()

    def test_ZCacheManager_getCache(self):
        root, cachemanager = self._makeContext()
        cache = cachemanager.ZCacheManager_getCache()
        self.assert_(isinstance(cache, AcceleratedHTTPCache))

    def test_getSettings(self):
        root, cachemanager = self._makeContext()
        settings = cachemanager.getSettings()
        self.assert_('anonymous_only' in settings.keys())
        self.assert_('interval' in settings.keys())
        self.assert_('notify_urls' in settings.keys())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AcceleratedHTTPCacheTests))
    suite.addTest(unittest.makeSuite(CacheManagerTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

