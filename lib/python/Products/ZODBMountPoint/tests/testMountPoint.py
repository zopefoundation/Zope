##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Tests of DBTab and ZODBMountPoint
"""

import os
import sys
import unittest
import Testing
import ZODB
import transaction
from OFS.Application import Application
from OFS.Folder import Folder
import App.config
from Products.ZODBMountPoint.MountedObject import manage_addMounts, getMountPoint
from DBTab.DBTab import DBTab

try:
    __file__
except NameError:
    __file__ = os.path.abspath(sys.argv[0])

class TestDBConfig:
    def __init__(self, fname, mpoints):
        self.fname = fname
        self.mpoints = mpoints
        
    def getDB(self):
        from ZODB.config import DemoStorage
        from ZODB.Connection import Connection
        from Zope2.Startup.datatypes import ZopeDatabase
        self.name = self.fname
        self.base = None
        self.path = os.path.join(os.path.dirname(__file__),  self.fname)
        self.create = None
        self.read_only = None
        self.quota = None
        self.cache_size = 5000
        self.pool_size = 7
        self.version_pool_size = 3
        self.version_cache_size = 100
        self.mount_points = self.mpoints
        self.connection_class = Connection
        self.class_factory = None
        self.storage = DemoStorage(self)
        self.container_class = None
        return ZopeDatabase(self)

    def getSectionName(self):
        return self.name

original_config = None

class DBTabTests (unittest.TestCase):

    

    def setUp(self):
        global original_config
        if original_config is None:
            # stow away original config so we can reset it
            original_config = App.config.getConfiguration()
            
        databases = [TestDBConfig('test_main.fs', ['/']).getDB(),
                     TestDBConfig('test_mount1.fs', ['/mount1']).getDB(),
                     TestDBConfig('test_mount2.fs', ['/mount2']).getDB(),
                     ]
        mount_points = {}
        mount_factories = {}
        for database in databases:
            points = database.getVirtualMountPaths()
            name = database.config.getSectionName()
            mount_factories[name] = database
            for point in points:
                mount_points[point] = name
        conf = DBTab(mount_factories, mount_points)
        d = App.config.DefaultConfiguration()
        d.dbtab = conf
        App.config.setConfiguration(d)
        self.conf = conf
        db = conf.getDatabase('/')
        self.db = db
        conn = db.open()
        root = conn.root()
        root['Application'] = app = Application()
        self.app = app
        transaction.commit()  # Get app._p_jar set
        manage_addMounts(app, ('/mount1', '/mount2'))
        transaction.commit()  # Get the mount points ready



    def tearDown(self):
        App.config.setConfiguration(original_config)
        transaction.abort()
        self.app._p_jar.close()
        del self.app
        del self.db
        for db in self.conf.opened.values():
            db.close()
        del self.conf

    def testRead(self):
        self.assertEqual(self.app.mount1.id, 'mount1')
        self.assertEqual(self.app.mount2.id, 'mount2')


    def testWrite(self):
        app = self.app
        app.mount1.a1 = '1'
        app.mount2.a2 = '2'
        app.a3 = '3'
        self.assertEqual(app.mount1._p_changed, 1)
        self.assertEqual(app.mount2._p_changed, 1)
        self.assertEqual(app._p_changed, 1)
        transaction.commit()
        self.assertEqual(app.mount1._p_changed, 0)
        self.assertEqual(app.mount2._p_changed, 0)
        self.assertEqual(app._p_changed, 0)


    def testRaceOnClose(self):
        # There used to be a race condition in
        # ConnectionPatches.close().  The root connection was returned
        # to the pool before the mounted connections were closed.  If
        # another thread pulled the root connection out of the pool
        # before the original thread finished closing mounted
        # connections, when the original thread got control back it
        # closed the mounted connections even though the new thread
        # was using them.

        # Test by patching to watch for a vulnerable moment.

        from ZODB.DB import DB

        def _closeConnection(self, connection):
            self._real_closeConnection(connection)
            mc = connection._mounted_connections
            if mc is not None:
                for c in mc.values():
                    if c._storage is not None:
                        raise AssertionError, "Connection remained partly open"

        DB._real_closeConnection = DB._closeConnection
        DB._closeConnection = _closeConnection
        try:
            conn = self.db.open()
            conn.root()['Application']['mount1']
            conn.root()['Application']['mount2']
            conn.close()
        finally:
            DB._closeConnection = DB._real_closeConnection
            del DB._real_closeConnection


    def testGetMountPoint(self):
        self.assert_(getMountPoint(self.app) is None)
        self.assert_(getMountPoint(self.app.mount1) is not None)
        self.assertEqual(getMountPoint(self.app.mount1)._path, '/mount1')
        self.assert_(getMountPoint(self.app.mount2) is not None)
        self.assertEqual(getMountPoint(self.app.mount2)._path, '/mount2')
        del self.app.mount2
        self.app.mount2 = Folder()
        self.app.mount2.id = 'mount2'
        self.assert_(getMountPoint(self.app.mount2) is None)
        transaction.commit()
        self.assert_(getMountPoint(self.app.mount2) is None)


def test_suite():
    return unittest.makeSuite(DBTabTests, 'test')

if __name__ == '__main__':
    unittest.main()

