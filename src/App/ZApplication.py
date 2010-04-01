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

import transaction

connection_open_hooks = []

class ZApplicationWrapper:

    def __init__(self, db, name, klass= None, klass_args=()):
        self._stuff = db, name
        if klass is not None:
            conn=db.open()
            root=conn.root()
            if not root.has_key(name):
                root[name]=klass()
                transaction.commit()
            conn.close()
            self._klass=klass

    # This hack is to overcome a bug in Bobo!
    def __getattr__(self, name):
        return getattr(self._klass, name)

    def __bobo_traverse__(self, REQUEST=None, name=None):
        db, aname = self._stuff
        conn = db.open()

        if connection_open_hooks:
            for hook in connection_open_hooks:
                hook(conn)

        # arrange for the connection to be closed when the request goes away
        cleanup = Cleanup(conn)
        REQUEST._hold(cleanup)

        conn.setDebugInfo(REQUEST.environ, REQUEST.other)

        v=conn.root()[aname]

        if name is not None:
            if hasattr(v, '__bobo_traverse__'):
                return v.__bobo_traverse__(REQUEST, name)

            if hasattr(v,name): return getattr(v,name)
            return v[name]

        return v


    def __call__(self, connection=None):
        db, aname = self._stuff

        if connection is None:
            connection=db.open()
        elif isinstance(connection, basestring):
            connection=db.open(connection)

        return connection.root()[aname]


class Cleanup:
    def __init__(self, jar):
        self._jar = jar

    def __del__(self):
        transaction.abort()
        self._jar.close()
