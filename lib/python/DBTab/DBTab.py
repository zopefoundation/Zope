##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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
"""DBTab and DatabaseFactory classes.

$Id$
"""

import sys
from thread import allocate_lock

from ZODB.ActivityMonitor import ActivityMonitor
import Globals

from Exceptions import DBTabConfigurationError


class DBTab:
    """A Zope database configuration, similar in purpose to /etc/fstab.
    """

    def __init__(self, db_factories, mount_paths):
        self._started = 0
        self.opened = {}            # { name -> Database instance }
        self.lock = allocate_lock()

        self.db_factories = db_factories  # { name -> DatabaseFactory }
        self.mount_paths = mount_paths    # { virtual path -> name }

    def startup(self):
        """Opens the databases set to open_at_startup."""
        if self._started:
            return
        self._started = 1
        for name, factory in self.db_factories.items():
            if factory.getOpenAtStartup():
                self.getDatabase(name=name)

    def listMountPaths(self):
        """Returns a sequence of (virtual_mount_path, database_name).
        """
        return self.mount_paths.items()


    def listDatabaseNames(self):
        """Returns a sequence of names.
        """
        return self.db_factories.keys()


    def hasDatabase(self, name):
        """Returns true if name is the name of a configured database."""
        return self.db_factories.has_key(name)


    def _mountPathError(self, mount_path):
        if mount_path == '/':
            raise DBTabConfigurationError(
                "No root database configured")
        else:
            raise DBTabConfigurationError(
                "No database configured for mount point at %s"
                % mount_path)


    def getDatabase(self, mount_path=None, name=None, is_root=0):
        """Returns an opened database.  Requires either mount_path or name.
        """
        self.startup()
        if name is None:
            if mount_path is None:
                raise ValueError('Either mount_path or name is required')
            name = self.mount_paths.get(mount_path)
            if name is None:
                self._mountPathError(mount_path)
        db = self.opened.get(name)
        if db is None:
            if not self.db_factories.has_key(name):
                raise KeyError('%s is not a configured database' % repr(name))
            self.lock.acquire()
            try:
                # Check again, since the database may have been created
                # by another thread before the lock was acquired.
                db = self.opened.get(name)
                if db is None:
                    db = self._createDatabase(name, is_root)
            finally:
                self.lock.release()
        return db

    def getDatabaseFactory(self, mount_path=None, name=None):
        if name is None:
            if mount_path is None:
                raise ValueError('Either mount_path or name is required')
            name = self.mount_paths.get(mount_path)
            if name is None:
                self._mountPathError(mount_path)
        return self.db_factories[name]


    def _createDatabase(self, name, is_root):
        factory = self.db_factories[name]
        db = factory.open()
        self.opened[name] = db
        if not is_root:
            Globals.opened.append(db)
        # If it is the root database, Zope will add the database to
        # Globals.opened.  A database should not be listed twice.
        return db

