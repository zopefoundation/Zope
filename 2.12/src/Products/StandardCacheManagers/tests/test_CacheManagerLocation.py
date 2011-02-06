##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
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

import transaction
import zope.component

from zope.component import testing as componenttesting
from zope.component import eventtesting

from AccessControl import SecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from OFS.Folder import Folder
from OFS.tests.testCopySupport import CopySupportTestBase
from OFS.tests.testCopySupport import UnitTestSecurityPolicy
from OFS.tests.testCopySupport import UnitTestUser

from Products.Five import zcml
from Products.StandardCacheManagers.RAMCacheManager import RAMCacheManager
from Products.StandardCacheManagers.AcceleratedHTTPCacheManager \
     import AcceleratedHTTPCacheManager
import Products.StandardCacheManagers

CACHE_META_TYPES = tuple(dict(name=instance_class.meta_type,
                              action='unused_constructor_name',
                              permission="Add %ss" % instance_class.meta_type)
                         for instance_class in (RAMCacheManager,
                                                AcceleratedHTTPCacheManager)
                         )

class CacheManagerLocationTests(CopySupportTestBase):

    _targetClass = None

    def _makeOne(self, *args, **kw):
        return self._targetClass(*args, **kw)

    def setUp( self ):
        componenttesting.setUp()
        eventtesting.setUp()
        zcml.load_config('meta.zcml', zope.component)
        zcml.load_config('configure.zcml', Products.StandardCacheManagers)

        folder1, folder2 = self._initFolders()

        folder1.all_meta_types = folder2.all_meta_types = CACHE_META_TYPES

        self.folder1 = folder1
        self.folder2 = folder2

        self.policy = UnitTestSecurityPolicy()
        self.oldPolicy = SecurityManager.setSecurityPolicy( self.policy )

        cm_id = 'cache'
        manager = self._makeOne(cm_id)
        self.folder1._setObject(cm_id, manager)
        self.cachemanager = self.folder1[cm_id]
        transaction.savepoint(optimistic=True)

        newSecurityManager( None, UnitTestUser().__of__( self.root ) )

        CopySupportTestBase.setUp(self)

    def tearDown( self ):

        noSecurityManager()
        SecurityManager.setSecurityPolicy( self.oldPolicy )
        del self.oldPolicy
        del self.policy
        del self.folder2
        del self.folder1

        self._cleanApp()
        componenttesting.tearDown()
        CopySupportTestBase.tearDown(self)

    def test_cache_differs_on_copy(self):
        # ensure copies don't hit the same cache
        cache = self.cachemanager.ZCacheManager_getCache()
        cachemanager_copy = self.folder2.manage_clone(self.cachemanager,
                                                      'cache_copy')
        cache_copy = cachemanager_copy.ZCacheManager_getCache()
        self.assertNotEqual(cache, cache_copy)

    def test_cache_remains_on_move(self):
        # test behaviour of cache on move.
        # NOTE: This test verifies current behaviour, but there is no actual
        # need for cache managers to maintain the same cache on move.
        # if physical path starts being used as a cache key, this test might
        # need to be fixed.
        cache = self.cachemanager.ZCacheManager_getCache()
        cut = self.folder1.manage_cutObjects(['cache'])
        self.folder2.manage_pasteObjects(cut)
        cachemanager_moved = self.folder2['cache']
        cache_moved = cachemanager_moved.ZCacheManager_getCache()
        self.assertEqual(cache, cache_moved)

    def test_cache_deleted_on_remove(self):
        old_cache = self.cachemanager.ZCacheManager_getCache()
        self.folder1.manage_delObjects(['cache'])
        new_cache = self.cachemanager.ZCacheManager_getCache()
        self.assertNotEqual(old_cache, new_cache)

class AcceleratedHTTPCacheManagerLocationTests(CacheManagerLocationTests):

    _targetClass = AcceleratedHTTPCacheManager

class RamCacheManagerLocationTests(CacheManagerLocationTests):

    _targetClass = RAMCacheManager

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AcceleratedHTTPCacheManagerLocationTests))
    suite.addTest(unittest.makeSuite(RamCacheManagerLocationTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

