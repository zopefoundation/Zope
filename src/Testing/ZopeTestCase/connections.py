##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZODB connection registry
"""


class ConnectionRegistry:
    '''ZODB connection registry

    This registry can hold either ZODB.Connection objects or OFS.Application
    objects. In the latter case, a close operation will close the REQUEST as
    well as the Connection referenced by the Application's _p_jar attribute.
    '''

    def __init__(self):
        self._conns = []

    def register(self, conn):
        self._conns.append(conn)

    def contains(self, conn):
        return conn in self._conns

    def __len__(self):
        return len(self._conns)

    def count(self):
        return len(self)

    def close(self, conn):
        if self.contains(conn):
            self._conns.remove(conn)
        self._do_close(conn)

    def closeAll(self):
        for conn in self._conns:
            self._do_close(conn)
        self._conns = []

    def _do_close(self, conn):
        if hasattr(conn, 'close'):
            conn.close()
        else:
            conn.REQUEST.close()
            conn._p_jar.close()


registry = ConnectionRegistry()
register = registry.register
contains = registry.contains
count = registry.count
close = registry.close
closeAll = registry.closeAll
