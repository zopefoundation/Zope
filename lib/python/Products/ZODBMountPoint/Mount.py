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
"""ZODB Mounted database support, simplified for DBTab.

$Id: Mount.py,v 1.5 2004/04/20 14:38:52 andreasjung Exp $"""

import sys
from logging import getLogger

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import traceback

import Persistence, Acquisition
from Acquisition import aq_base
from ZODB.POSException import MountedStorageError

from ZODB.DB import DB
from ZODB.Connection import Connection

LOG = getLogger('Zope.ZODBMountPoint')

class MountPoint(Persistence.Persistent, Acquisition.Implicit):
    """An object that accesses a different database when traversed.

    This class is intended to be used as a base class.
    """

    # Default values for non-persistent variables.
    _v_data = None   # An object in an open connection
    _v_connect_error = None

    def __init__(self, id):
        self.id = id

    def _getDB(self):
        """Hook for getting the DB object for this mount point."""
        raise NotImplementedError

    def _getDBName(self):
        """Hook for getting the name of the database for this mount point."""
        raise NotImplementedError

    def _getRootDBName(self):
        """Hook for getting the name of the root database."""
        raise NotImplementedError

    def _traverseToMountedRoot(self, root, mount_parent):
        """Hook for getting the object to be mounted."""
        raise NotImplementedError

    def __repr__(self):
        return "%s(id=%s)" % (self.__class__.__name__, repr(self.id))


    def _getMountedConnection(self, anyjar):
        db_name = self._getDBName()
        conn = anyjar._getMountedConnection(db_name)
        if conn is None:
            root_conn = anyjar._getRootConnection()
            if db_name == self._getRootDBName():
                conn = root_conn
            else:
                conn = self._getDB().open(version=root_conn.getVersion())
                root_conn._addMountedConnection(db_name, conn)
        return conn


    def _getOrOpenObject(self, parent):
        t = self._v_data
        if t is not None:
            data = t[0]
        else:
            self._v_connect_error = None
            conn = None
            try:
                anyjar = self._p_jar
                if anyjar is None:
                    anyjar = parent._p_jar
                conn = self._getMountedConnection(anyjar)
                root = conn.root()
                obj = self._traverseToMountedRoot(root, parent)
                data = aq_base(obj)
                # Store the data object in a tuple to hide from acquisition.
                self._v_data = (data,)
            except:
                # Possibly broken database.
                self._logConnectException()
                raise

            try:
                # XXX This method of finding the mount point is deprecated.
                # Do not use the _v_mount_point_ attribute.
                data._v_mount_point_ = (aq_base(self),)
            except:
                # Might be a read-only object.
                pass

        return data.__of__(parent)


    def __of__(self, parent):
        # Accesses the database, returning an acquisition
        # wrapper around the connected object rather than around self.
        try:
            return self._getOrOpenObject(parent)
        except:
            return Acquisition.ImplicitAcquisitionWrapper(self, parent)


    def _test(self, parent):
        """Tests the database connection."""
        self._getOrOpenObject(parent)
        return 1


    def _logConnectException(self):
        """Records info about the exception that just occurred."""
        exc = sys.exc_info()
        LOG.error('Failed to mount database. %s (%s)' % exc[:2], exc_info=exc)
        f=StringIO()
        traceback.print_tb(exc[2], 100, f)
        self._v_connect_error = (exc[0], exc[1], f.getvalue())
        exc = None

class MountConnection(Connection):
    """Subclass of Connection that supports mounts."""

    # XXX perhaps the code in this subclass should be folded into
    # ZODB proper.

    def __init__(self, **kwargs):
        Connection.__init__(self, **kwargs)
        # The _root_connection of the actual root points to self.  All
        # other connections will have _root_connection over-ridden in
        # _addMountedConnection().
        self._root_connection = self
        self._mounted_connections = {}
        
    def _getRootConnection(self):
        return self._root_connection

    def _getMountedConnection(self, name):
        return self._root_connection._mounted_connections.get(name)

    def _addMountedConnection(self, name, conn):
        if conn._root_connection is not conn:
            raise ValueError("Connection %s is already mounted" % repr(conn))
        conns = self._root_connection._mounted_connections
        if name in conns:
            raise KeyError("A connection named %s already exists" % repr(name))
        conn._root_connection = self._root_connection
        conns[name] = conn

    def _setDB(self, odb, **kwargs):
        Connection._setDB(self, odb, **kwargs)
        for conn in self._mounted_connections.values():
            conn._setDB(odb, **kwargs)

    def close(self):
        if self._root_connection is not self:
            raise RuntimeError("Should not close mounted connections directly")

        # The code here duplicates much of the code in
        # DB._closeConnection and Connection.close.  A mounted
        # connection can't operate independently, so we don't call
        # DB._closeConnection(), which would return it to the
        # connection pool; only the root connection should be
        # returned.
        
        for conn in self._mounted_connections.values():
            # DB._closeConnection calls the activity monitor
            am = conn._db.getActivityMonitor()
            am.closedConnection(conn)
            # Connection.close does GC
            conn._cache.incrgc()
            conn._storage = conn._tmp = conn.new_oid = conn._opened = None
            conn._debug_info = ()
            # The mounted connection keeps a reference to
            # its database, but nothing else.
            
        # Close this connection only after the mounted connections
        # have been closed.  Otherwise, this connection gets returned
        # to the pool too early and another thread might use this
        # connection before the mounted connections have all been
        # closed.
        Connection.close(self)

# Replace the default database Connection
def install():
    DB.klass = MountConnection
    
# XXX This shouldn't be done as a side-effect of import, but it's not
# clear where in the Zope initialization code it should be done.
install()
