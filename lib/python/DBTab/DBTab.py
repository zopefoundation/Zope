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

from ZODB.ActivityMonitor import ActivityMonitor
import Globals

from Exceptions import DBTabConfigurationError


class DBTab:
    """A Zope database configuration, similar in purpose to /etc/fstab.
    """

    def __init__(self, db_factories, mount_paths):
        self._started = 0

        self.db_factories = db_factories  # { name -> DatabaseFactory }
        self.mount_paths = mount_paths    # { virtual path -> name }
        self.databases = {}

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
        self.startup() # XXX get rid of this
        if name is None:
            name = self.getName(mount_path)
        db = self.databases.get(name, None)
        if db is None:
            factory = self.getDatabaseFactory(name=name)
            db = factory.open(name, self.databases)
        return db

    def getDatabaseFactory(self, mount_path=None, name=None):
        if name is None:
            name = self.getName(mount_path)
        if not self.db_factories.has_key(name):
            raise KeyError('%s is not a configured database' % repr(name))
        return self.db_factories[name]

    def getName(self, mount_path):
        name = self.mount_paths.get(mount_path)
        if name is None:
            self._mountPathError(mount_path)
        return name

