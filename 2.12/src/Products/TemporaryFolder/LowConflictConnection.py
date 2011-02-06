##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from ZODB.Connection import Connection
from ZODB.POSException import ConflictError
from cPickle import Unpickler
from cStringIO import StringIO

class LowConflictConnection(Connection):
    def setstate(self, object):
        """
        Unlike the 'stock' Connection class' setstate, this method
        doesn't raise ConflictErrors.  This is potentially dangerous
        for applications that need absolute consistency, but
        sessioning is not one of those.
        """
        oid=object._p_oid
        invalid = self._invalid
        if invalid(None):
            # only raise a conflict if there was
            # a mass invalidation, but not if we see this
            # object's oid as invalid
            raise ConflictError, `oid`
        p, serial = self._storage.load(oid, self._version)
        file=StringIO(p)
        unpickler=Unpickler(file)
        unpickler.persistent_load=self._persistent_load
        unpickler.load()
        state = unpickler.load()
        if hasattr(object, '__setstate__'):
            object.__setstate__(state)
        else:
            d=object.__dict__
            for k,v in state.items(): d[k]=v
        object._p_serial=serial
