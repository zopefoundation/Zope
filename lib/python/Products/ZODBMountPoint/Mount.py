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

$Id$"""

import sys
from logging import getLogger

try:
    from cStringIO import StringIO
except:
    from StringIO import StringIO
import traceback

import Persistence, Acquisition
from Acquisition import aq_base
from ZODB.POSException import MountedStorageError, ConnectionStateError


LOG = getLogger('Zope.ZODBMountPoint')

class MountPoint(Persistence.Persistent, Acquisition.Implicit):
    '''The base class for a Zope object which, when traversed,
    accesses a different database.
    '''

    # Default values for non-persistent variables.
    _v_data = None   # An object in an open connection
    _v_connect_error = None

    def __init__(self, id):
        self.id = id

    def _getDB(self):
        """Hook for getting the DB object for this mount point.
        """
        raise NotImplementedError

    def _getDBName(self):
        """Hook for getting the name of the database for this mount point.
        """
        raise NotImplementedError

    def _getRootDBName(self):
        """Hook for getting the name of the root database.
        """
        raise NotImplementedError

    def _traverseToMountedRoot(self, root, mount_parent):
        """Hook for getting the object to be mounted.
        """
        raise NotImplementedError

    def __repr__(self):
        return "%s(id=%s)" % (self.__class__.__name__, repr(self.id))


    def _getMountedConnection(self, anyjar):
        db_name = self._getDBName()
        conn = anyjar.get_connection(db_name)
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
        '''Tests the database connection.
        '''
        self._getOrOpenObject(parent)
        return 1


    def _logConnectException(self):
        '''Records info about the exception that just occurred.
        '''
        try:
            from cStringIO import StringIO
        except:
            from StringIO import StringIO
        import traceback
        exc = sys.exc_info()
        LOG.error('Failed to mount database. %s (%s)' % exc[:2], exc_info=exc)
        f=StringIO()
        traceback.print_tb(exc[2], 100, f)
        self._v_connect_error = (exc[0], exc[1], f.getvalue())
        exc = None
