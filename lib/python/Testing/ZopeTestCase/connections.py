##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
"""

class ConnectionRegistry:
    '''ZODB connection registry'''

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
        conn.close()

    def closeAll(self):
        for conn in self._conns:
            conn.close()
        self._conns = []


registry = ConnectionRegistry()
register = registry.register
contains = registry.contains
count = registry.count
close = registry.close
closeAll = registry.closeAll

