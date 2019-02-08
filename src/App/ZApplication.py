##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Implement an bobo_application object that is BoboPOS3 aware

This module provides a wrapper that causes a database connection to be created
and used when bobo publishes a bobo_application object.
"""

import sys


if sys.version_info >= (3, ):
    basestring = str


class ZApplicationWrapper(object):

    def __init__(self, db, name, klass=None):
        self._db = db
        self._name = name
        if klass is not None:
            conn = db.open()
            root = conn.root()
            if name not in root:
                root[name] = klass()
                conn.transaction_manager.commit()
            conn.close()
            self._klass = klass

    # This hack is to overcome a bug in Bobo!
    def __getattr__(self, name):
        return getattr(self._klass, name)

    def __bobo_traverse__(self, REQUEST=None, name=None):
        # This is only called by ZServer.ZPublisher.Publish,
        # as the app in the module_info is used directly.

        conn = self._db.open()

        # arrange for the connection to be closed when the request goes away
        cleanup = Cleanup(conn)
        REQUEST._hold(cleanup)

        conn.setDebugInfo(REQUEST.environ, REQUEST.other)

        v = conn.root()[self._name]

        if name is not None:
            if hasattr(v, '__bobo_traverse__'):
                return v.__bobo_traverse__(REQUEST, name)

            if hasattr(v, name):
                return getattr(v, name)
            return v[name]

        return v

    def __call__(self, connection=None):
        # This is only called by ZPublisher.WSGIPublisher,
        # as load_app calls the app object present in the module_info.

        db = self._db
        if connection is None:
            connection = db.open()
        elif isinstance(connection, basestring):
            connection = db.open(connection)

        return connection.root()[self._name]


class Cleanup(object):
    def __init__(self, jar):
        self._jar = jar

    def __del__(self):
        if self._jar.transaction_manager._txn is not None:
            # Only abort a transaction, if one exists. Otherwise the
            # abort creates a new transaction just to abort it.
            self._jar.transaction_manager.abort()
        self._jar.close()
