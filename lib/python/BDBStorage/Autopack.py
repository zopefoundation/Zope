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

"""An autopacking Berkeley storage without undo and versioning.
"""
__version__ = '$Revision: 1.1 $'.split()[-2:][0]

import sys
import struct
import time

# This uses the Dunn/Kuchling PyBSDDB v3 extension module available from
# http://pybsddb.sourceforge.net
from bsddb3 import db

from ZODB import POSException
from ZODB.utils import p64, U64
from ZODB.referencesf import referencesf
from ZODB.TimeStamp import TimeStamp
#from ZODB.ConflictResolution import ConflictResolvingStorage, ResolvedSerial
import ThreadLock

# BerkeleyBase.BerkeleyBase class provides some common functionality for all
# the Berkeley DB based storages.  It in turn inherits from
# ZODB.BaseStorage.BaseStorage which itself provides some common storage
# functionality.
from BerkeleyBase import BerkeleyBase

ZERO = '\0'*8
INC = 'I'
DEC = 'D'



class Autopack(BerkeleyBase):
    def _setupDBs(self):
        # Data Type Assumptions:
        #
        # object ids (oid) are 8-bytes
        # object serial numbers are 8-bytes
        # transaction ids (tid) are 8-bytes
        # revision ids (revid) are the same as transaction ids, just used in a
        #     different context.
        # version ids (vid) are 8-bytes
        # data pickles are of arbitrary length
        #
        # Create the tables used to maintain the relevant information.  The
        # full storage needs a bunch of tables.  These two are defined by the
        # base class infrastructure and are shared by the Minimal
        # implementation.
        #
        # serials -- {oid -> serial}
        #     Maps oids to object serial numbers.  The serial number is
        #     essentially a timestamp used to determine if conflicts have
        #     arisen, and serial numbers double as transaction ids and object
        #     revision ids.  If an attempt is made to store an object with a
        #     serial number that is different than the current serial number
        #     for the object, a ConflictError is raised.
        #
        # pickles -- {oid+revid -> pickle}
        #     Maps the concrete object referenced by oid+revid to that
        #     object's data pickle.
        #
        # These are used only by the Autopack implementation.
        #
        # refcounts -- {oid -> count}
        #     Maps objects to their reference counts.
        #
        # actions -- {tid+oid -> action}
        #     A mapping of transaction id and oid to an `action'.  Actions are
        #     reference counting actions INC and DEC.
        #
        # oids -- {oid -> ' '}
        #     A set of all the oids stored in the current transaction (a
        #     performance optimization on abort()).
        #
        # Tables common to the base framework 
        self._serials = self._setupDB('serials')
        self._pickles = self._setupDB('pickles')
        # These are specific to the Autopack implementation
        self._refcounts = self._setupDB('refcounts')
        self._actions = self._setupDB('actions', db.DB_DUP)
        self._oids = self._setupDB('oids')
        # DEBUGGING
        #self._nextserial = 0L
        
    def close(self):
        self._serials.close()
        self._pickles.close()
        self._refcounts.close()
        self._actions.close()
        self._oids.close()
        BerkeleyBase.close(self)

    def _begin(self, tid, u, d, e):
        # Nothing needs to be done
        pass

    def _vote(self):
        # Nothing needs to be done, but override the base class's method
        pass

    def _finish(self, tid, u, d, e):
        # TBD: what about u, d, and e?
        #
        # First, append a DEL to the actions for each old object, then update
        # the current serials table so that its revision id points to this
        # trancation id.
        txn = self._env.txn_begin()
        try:
            c = self._oids.cursor()
            try:
                rec = c.first()
                while 1:
                    if rec is None:
                        break
                    oid, data = rec
                    lastrevid = self._serials.get(oid, txn=txn)
                    if lastrevid:
                        self._actions.put(lastrevid+oid, DEC, txn=txn)
                    self._serials.put(oid, tid, txn=txn)
                    rec = c.next()
            finally:
                c.close()
        except:
            txn.abort()
            raise
        else:
            txn.commit()
        self._oids.truncate()

    # Override BerkeleyBase._abort()
    def _abort(self):
        # Add actions to decref object pickle data so they'll be deleted from
        # the _pickles table on the next autopack.  This is why the actions
        # table has serials before oid in its key.
        tid = self._serial
        txn = self._env.txn_begin()
        try:
            c = self._oids.cursor()
            try:
                rec = c.first()
                while 1:
                    if rec is None:
                        break
                    oid, data = rec
                    self._actions.put(tid+oid, DEC, txn=txn)
                    rec = c.next()
            finally:
                c.close()
        except:
            txn.abort()
            raise
        else:
            txn.commit()
        self._oids.truncate()
        self._transaction.abort()

    def store(self, oid, serial, data, version, transaction):
        # Transaction guard
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)
        # We don't support versions
        if version <> '':
            raise POSException.Unsupported, 'versions are not supported'
        oserial = self._serials.get(oid)
        if oserial is not None and serial <> oserial:
            # BAW: Here's where we'd try to do conflict resolution
            raise POSException.ConflictError(serials=(oserial, serial))
        tid = self._serial
        txn = self._env.txn_begin()
        try:
            self._pickles.put(oid+tid, data, txn=txn)
            self._actions.put(tid+oid, INC, txn=txn)
            self._oids.put(oid, ' ', txn=txn)
        except:
            txn.abort()
            raise
        else:
            txn.commit()
        return self._serial

    def load(self, oid, version):
        if version <> '':
            raise POSException.Unsupported, 'versions are not supported'
        current = self._serials[oid]
        return self._pickles[oid+current], current

    def loadSerial(self, oid, serial):
        current = self._serials[oid]
        if current == serial:
            return self._pickles[oid+current]
        else:
            raise KeyError

    def getSerial(self, oid):
        return self._serials[oid]

    def iterator(self):
        raise NotImplementedError

    # Not part of the storage API

    def autopack(self):
        raise NotImplementedError
