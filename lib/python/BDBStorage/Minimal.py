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

"""Berkeley storage without undo or versioning.
"""

__version__ = '$Revision: 1.13 $'[-2:][0]

# This uses the Dunn/Kuchling PyBSDDB v3 extension module available from
# http://pybsddb.sourceforge.net.  It is compatible with release 3.4 of
# PyBSDDB3.
from bsddb3 import db

# BerkeleyBase class provides some common functionality for BerkeleyDB-based
# storages.  It in turn inherits from BaseStorage which itself provides some
# common storage functionality.
from BerkeleyBase import BerkeleyBase
from ZODB import POSException
from ZODB.utils import U64, p64
from ZODB.referencesf import referencesf

ABORT = 'A'
COMMIT = 'C'
PRESENT = 'X'
ZERO = '\0'*8



class Minimal(BerkeleyBase):
    def _setupDBs(self):
        # Data Type Assumptions:
        #
        # - Object ids (oid) are 8-bytes
        # - Objects have revisions, with each revision being identified by a
        #   unique serial number.
        # - Transaction ids (tid) are 8-bytes
        # - Data pickles are of arbitrary length
        #
        # The Minimal storage uses the following tables:
        #
        # serials -- {oid -> [serial]}
        #     Maps oids to serial numbers.  Each oid can be mapped to 1 or 2
        #     serial numbers (this is for optimistic writes).  If it maps to
        #     two serial numbers, then the current one is determined by the
        #     pending flag (see below).
        #
        # pickles -- {oid+serial -> pickle}
        #     Maps the object revisions to the revision's pickle data.
        #
        # refcounts -- {oid -> count}
        #     Maps the oid to the reference count for the object.  This
        #     reference count is updated during the _finish() call.  When it
        #     goes to zero, the object is automatically deleted.
        #
        # oids -- [oid]
        #     This is a list of oids of objects that are modified in the
        #     current uncommitted transaction.
        #
        # pending -- tid -> 'A' | 'C'
        #     This is an optional flag which says what to do when the database
        #     is recovering from a crash.  The flag is normally 'A' which
        #     means any pending data should be aborted.  At the start of the
        #     tpc_finish() this flag will be changed to 'C' which means, upon
        #     recovery/restart, all pending data should be committed.  Outside
        #     of any transaction (e.g. before the tpc_begin()), there will be
        #     no pending entry.  It is a database invariant that if the
        #     pending table is empty, the oids table must also be empty.
        #
        self._serials = self._setupDB('serials', db.DB_DUP)
        self._pickles = self._setupDB('pickles')
        self._refcounts = self._setupDB('refcounts')
        self._oids = self._setupDB('oids')
        self._pending = self._setupDB('pending')
        # Do recovery and consistency checks
        pendings = self._pending.keys()
        assert len(pendings) <= 1
        if len(pendings) == 0:
            assert len(self._oids) == 0
            return
        # Do recovery
        tid = pendings[0]
        flag = self._pending.get(tid)
        assert flag in (ABORT, COMMIT)
        self._lock_acquire()
        try:
            if flag == ABORT:
                self._do(self._doabort, tid)
            else:
                self._do(self._docommit, tid)
        finally:
            self._lock_release()

    def close(self):
        self._serials.close()
        self._pickles.close()
        self._refcounts.close()
        self._oids.close()
        self._pending.close()
        BerkeleyBase.close(self)

    def _do(self, meth, tid):
        txn = self._env.txn_begin()
        try:
            meth(tid, txn)
            self._oids.truncate(txn)
            self._pending.truncate(txn)
        except:
            txn.abort()
            self._docheckpoint()
            raise
        else:
            txn.commit()
            self._docheckpoint()

    def _doabort(self, tid, txn):
        co = cs = None
        try:
            co = self._oids.cursor(txn=txn)
            cs = self._serials.cursor(txn=txn)
            rec = co.first()
            while rec:
                oid = rec[0]
                rec = co.next()
                try:
                    cs.set_both(oid, tid)
                except db.DBNotFoundError:
                    pass
                else:
                    cs.delete()
                # And delete the pickle table entry for this revision.
                self._pickles.delete(oid+tid, txn=txn)
        finally:
            # There's a small window of opportunity for leaking a cursor here,
            # if co.close() were to fail.  In practice this shouldn't happen.
            if co: co.close()
            if cs: cs.close()

    def _docommit(self, tid, txn):
        deltas = {}
        co = cs = None
        try:
            co = self._oids.cursor(txn=txn)
            cs = self._serials.cursor(txn=txn)
            rec = co.first()
            while rec:
                oid = rec[0]
                rec = co.next()
                # Remove from the serials table all entries with key oid where
                # the serial is not tid.  These are the old revisions of the
                # object.  At the same time, we want to collect the oids of
                # the objects referred to by this revision's pickle, so that
                # later we can decref those reference counts.
                srec = cs.set(oid)
                while srec:
                    soid, stid = srec
                    if soid <> oid:
                        break
                    if stid <> tid:
                        cs.delete()
                        data = self._pickles.get(oid+stid, txn=txn)
                        assert data is not None
                        self._update(deltas, data, -1)
                        self._pickles.delete(oid+stid, txn=txn)
                    srec = cs.next_dup()
                # Now add incref deltas for all objects referenced by the new
                # revision of this object.
                data = self._pickles.get(oid+tid, txn=txn)
                assert data is not None
                self._update(deltas, data, 1)
        finally:
            # There's a small window of opportunity for leaking a cursor here,
            # if co.close() were to fail.  In practice this shouldn't happen.
            if co: co.close()
            if cs: cs.close()
        # Now, to finish up, we need apply the refcount deltas to the
        # refcounts table, and do recursive collection of all refcount == 0
        # objects.
        while deltas:
            deltas = self._update_refcounts(deltas, txn)

    def _update_refcounts(self, deltas, txn):
        newdeltas = {}
        for oid, delta in deltas.items():
            rc = U64(self._refcounts.get(oid, ZERO, txn=txn)) + delta
            assert rc >= 0
            if rc == 0:
                # The reference count for this object has just gone to zero,
                # so we can safely remove all traces of it from the serials,
                # pickles and refcounts table.  Note that before we remove its
                # pickle, we need to decref all the objects referenced by it.
                current = self._getCurrentSerial(oid)
                data = self._pickles.get(oid+current, txn=txn)
                self._update(newdeltas, data, -1)
                # And delete the serials, pickle and refcount entries.  At
                # this point, I believe we should have just one serial entry.
                self._serials.delete(oid, txn=txn)
                assert self._serials.get(oid, txn=txn) is None
                self._refcounts.delete(oid, txn=txn)
                self._pickles.delete(oid+current, txn=txn)
            else:
                self._refcounts.put(oid, p64(rc), txn=txn)
        # Return the list of objects referenced by pickles just deleted in
        # this round, for decref'ing on the next go 'round.
        return newdeltas

    def _begin(self, tid, u, d, e):
        # When a transaction begins, we set the pending flag to ABORT,
        # meaning, if we crash between now and the time we vote, all changes
        # will be aborted.
        self._pending[self._serial] = ABORT

    def store(self, oid, serial, data, version, transaction):
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)
        # We don't support versions
        if version <> '':
            raise POSException.Unsupported, 'versions are not supported'
        # All updates must be done with the application lock acquired
        self._lock_acquire()
        try:
            oserial = self._getCurrentSerial(oid)
            if oserial is not None and serial <> oserial:
                # The object exists in the database, but the serial number
                # given in the call is not the same as the last stored serial
                # number.  Raise a ConflictError.
                #
                # BAW: do application level conflict resolution
                raise POSException.ConflictError(serials=(oserial, serial))
            # Optimistically write to the serials and pickles table.  Be sure
            # to also update the oids table for this object too.
            newserial = self._serial
            txn = self._env.txn_begin()
            try:
                self._serials.put(oid, newserial, txn=txn)
                self._pickles.put(oid+newserial, data, txn=txn)
                self._oids.put(oid, PRESENT, txn=txn)
            except:
                txn.abort()
                self._docheckpoint()
                raise
            else:
                txn.commit()
                self._docheckpoint()
        finally:
            self._lock_release()
        # Return the new serial number for the object
        return newserial

    def _finish(self, tid, u, d, e):
        # Twiddle the pending flag to COMMIT now since after the vote call, we
        # promise that the changes will be committed, no matter what.  The
        # recovery process will check this.
        self._pending[self._serial] = COMMIT
        self._do(self._docommit, self._serial)

    def _abort(self):
        self._do(self._doabort, self._serial)

    #
    # Accessor interface
    #

    def _getCurrentSerial(self, oid):
        # BAW: We must have the application level lock here.
        c = self._serials.cursor()
        try:
            # There can be zero, one, or two entries in the serials table for
            # this oid.  If there are no entries, raise a KeyError (we know
            # nothing about this object).
            #
            # If there is exactly one entry then this has to be the entry for
            # the object, regardless of the pending flag.
            #
            # If there are two entries, then we need to look at the pending
            # flag to decide which to return (there /better/ be a pending flag
            # set!).  If the pending flag is COMMIT then we've already voted
            # so the second one is the good one.  If the pending flag is ABORT
            # then we haven't yet committed to this transaction so the first
            # one is the good one.
            serials = []
            try:
                rec = c.set(oid)
            except db.DBNotFoundError:
                rec = None
            while rec:
                serials.append(rec[1])
                rec = c.next_dup()
            if not serials:
                return None
            if len(serials) == 1:
                return serials[0]
            pending = self._pending.get(self._serial)
            assert pending in (ABORT, COMMIT)
            if pending == ABORT:
                return serials[0]
            return serials[1]
        finally:
            c.close()

    def load(self, oid, version):
        if version <> '':
            raise POSException.Unsupported, 'versions are not supported'
        self._lock_acquire()
        try:
            # Get the current serial number for this object
            serial = self._getCurrentSerial(oid)
            if serial is None:
                raise KeyError, 'Object does not exist: %r' % oid
            # Get this revision's pickle data
            return self._pickles[oid+serial], serial
        finally:
            self._lock_release()

    def modifiedInVersion(self, oid):
        # So BaseStorage.getSerial() just works.  Note that this storage
        # doesn't support versions.
        return ''
