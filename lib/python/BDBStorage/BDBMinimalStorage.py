##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.
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

__version__ = '$Revision: 1.32 $'[-2:][0]

from ZODB import POSException
from ZODB.utils import p64, U64
from ZODB.referencesf import referencesf
from ZODB.ConflictResolution import ConflictResolvingStorage, ResolvedSerial

from BDBStorage import db, ZERO
from BerkeleyBase import BerkeleyBase, PackStop, _WorkThread

ABORT = 'A'
COMMIT = 'C'
PRESENT = 'X'

BDBMINIMAL_SCHEMA_VERSION = 'BM01'



class BDBMinimalStorage(BerkeleyBase, ConflictResolvingStorage):
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
        # info -- {key -> value}
        #     This table contains storage metadata information.  The keys and
        #     values are simple strings of variable length.   Here are the
        #     valid keys:
        #
        #         version - the version of the database (reserved for ZODB4)
        #
        # packmark -- [oid]
        #     Every object reachable from the root during a classic pack
        #     operation will have its oid present in this table.
        #
        # oidqueue -- [oid]
        #     This table is a Queue, not a BTree.  It is used during the mark
        #     phase of pack() and contains a list of oids for work to be done.
        #     It is also used during pack to list objects for which no more
        #     references exist, such that the objects can be completely packed
        #     away.
        #
        self._packing = False
        self._info = self._setupDB('info')
        self._serials = self._setupDB('serials', db.DB_DUP)
        self._pickles = self._setupDB('pickles')
        self._refcounts = self._setupDB('refcounts')
        self._oids = self._setupDB('oids')
        self._pending = self._setupDB('pending')
        # Tables to support packing.
        self._packmark = self._setupDB('packmark')
        self._oidqueue = self._setupDB('oidqueue', 0, db.DB_QUEUE, 8)
        # Do recovery and consistency checks
        pendings = self._pending.keys()
        assert len(pendings) <= 1
        if len(pendings) == 0:
            assert len(self._oids) == 0
        else:
            # Do recovery
            tid = pendings[0]
            flag = self._pending.get(tid)
            assert flag in (ABORT, COMMIT)
            self._lock_acquire()
            try:
                if flag == ABORT:
                    self._withtxn(self._doabort, tid)
                else:
                    self._withtxn(self._docommit, tid)
            finally:
                self._lock_release()

    def _version_check(self, txn):
        version = self._info.get('version')
        if version is None:
            self._info.put('version', BDBMINIMAL_SCHEMA_VERSION, txn=txn)
        elif version <> BDBMINIMAL_SCHEMA_VERSION:
            raise POSException.StorageSystemError(
                'incompatible storage version')

    def _make_autopacker(self, event):
        return _Autopack(self, event, self._config.frequency)

    def _doabort(self, txn, tid):
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
        # We're done with these tables
        self._oids.truncate(txn)
        self._pending.truncate(txn)

    def _abort(self):
        self._withtxn(self._doabort, self._serial)

    def _docommit(self, txn, tid):
        self._pending.put(self._serial, COMMIT, txn)
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
                        # This is the previous revision of the object, so
                        # decref its referents and clean up its pickles.
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
        # We're done with this table
        self._pending.truncate(txn)
        # If we're in the middle of a pack, we need to add to the packmark
        # table any objects that were modified in this transaction.
        # Otherwise, there's a race condition where mark might have happened,
        # then the object is added, then sweep runs, deleting the object
        # created in the interrim.
        if self._packing:
            for oid in self._oids.keys():
                self._packmark.put(oid, PRESENT, txn=txn)
        self._oids.truncate(txn)
        # Now, to finish up, we need apply the refcount deltas to the
        # refcounts table, and do recursive collection of all refcount == 0
        # objects.
        while deltas:
            deltas = self._update_refcounts(deltas, txn)

    def _update_refcounts(self, deltas, txn):
        newdeltas = {}
        for oid, delta in deltas.items():
            refcount = U64(self._refcounts.get(oid, ZERO, txn=txn)) + delta
            assert refcount >= 0
            if refcount == 0:
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
                self._refcounts.put(oid, p64(refcount), txn=txn)
        # Return the list of objects referenced by pickles just deleted in
        # this round, for decref'ing on the next go 'round.
        return newdeltas

    def _begin(self, tid, u, d, e):
        # When a transaction begins, we set the pending flag to ABORT,
        # meaning, if we crash between now and the time we vote, all changes
        # will be aborted.
        txn = self._env.txn_begin()
        try:
            self._pending.put(self._serial, ABORT, txn)
        except:
            txn.abort()
            raise
        else:
            txn.commit()

    def _dostore(self, txn, oid, serial, data):
        conflictresolved = False
        oserial = self._getCurrentSerial(oid)
        if oserial is not None and serial <> oserial:
            # The object exists in the database, but the serial number
            # given in the call is not the same as the last stored serial
            # number.  Raise a ConflictError.
            data = self.tryToResolveConflict(oid, oserial, serial, data)
            if data:
                conflictresolved = True
            else:
                raise POSException.ConflictError(serials=(oserial, serial))
        # Optimistically write to the serials and pickles table.  Be sure
        # to also update the oids table for this object too.
        newserial = self._serial
        self._serials.put(oid, newserial, txn=txn)
        self._pickles.put(oid+newserial, data, txn=txn)
        self._oids.put(oid, PRESENT, txn=txn)
        # If we're in the middle of a pack, we need to add these objects to
        # the packmark, so a specific race condition won't collect them.
        # E.g. we do a mark, then we do a store, then we sweep.  The objects
        # stored between the mark and sweep would get collected away.
        if self._packing:
            self._packmark.put(oid, PRESENT, txn=txn)
        # Return the new serial number for the object
        if conflictresolved:
            return ResolvedSerial
        return newserial

    def store(self, oid, serial, data, version, transaction):
        if self._is_read_only:
            raise POSException.ReadOnlyError()
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)
        # We don't support versions
        if version <> '':
            raise POSException.Unsupported, 'versions are not supported'
        # All updates must be done with the application lock acquired
        self._lock_acquire()
        try:
            return self._withtxn(self._dostore, oid, serial, data)
        finally:
            self._lock_release()

    def _finish(self, tid, u, d, e):
        # _docommit() twiddles the pending flag to COMMIT now since after the
        # vote call, we promise that the changes will be committed, no matter
        # what.  The recovery process will check this.
        self._withtxn(self._docommit, self._serial)

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

    #
    # Packing.  In Minimal storage, packing is only required to get rid of
    # object cycles, since there are no old object revisions.
    #

    def pack(self, t, zreferencesf):
        # For all intents and purposes, referencesf here is always going to be
        # the same as ZODB.referencesf.referencesf.  It's too much of a PITA
        # to pass that around to the helper methods, so just assert they're
        # the same.
        assert zreferencesf == referencesf
        self.log('classic pack started')
        # A simple wrapper around the bulk of packing, but which acquires a
        # lock that prevents multiple packs from running at the same time.
        self._packlock.acquire()
        # Before setting the packing flag to true, acquire the storage lock
        # and clear out the packmark table, in case there's any cruft left
        # over from the previous pack.
        def clear_packmark(txn):
            self._packmark.truncate(txn=txn)
        self._withlock(self._withtxn, clear_packmark)
        self._packing = True
        try:
            # We don't wrap this in _withtxn() because we're going to do the
            # operation across several Berkeley transactions, which allows
            # other work to happen (stores and reads) while packing is being
            # done.
            #
            # Also, we don't care about the pack time, since we don't need to
            # collect object revisions
            self._dopack()
        finally:
            self._packing = False
            self._packlock.release()
        self.log('classic pack finished')

    def _dopack(self):
        # Do a mark and sweep for garbage collection.  Calculate the set of
        # objects reachable from the root.  Anything else is a candidate for
        # having all their revisions packed away.  The set of reachable
        # objects lives in the _packmark table.
        self._withlock(self._withtxn, self._mark)
        # Now perform a sweep, using oidqueue to hold all object ids for
        # objects which are not root reachable as of the pack time.
        self._withlock(self._withtxn, self._sweep)
        # Once again, collect any objects with refcount zero due to the mark
        # and sweep garbage collection pass.
        self._withlock(self._withtxn, self._collect_objs)

    def _mark(self, txn):
        # Find the oids for all the objects reachable from the root.  To
        # reduce the amount of in-core memory we need do do a pack operation,
        # we'll save the mark data in the packmark table.  The oidqueue is a
        # BerkeleyDB Queue that holds the list of object ids to look at next,
        # and by using this we don't need to keep an in-memory dictionary.
        assert len(self._oidqueue) == 0
        # Quick exit for empty storages
        if not self._serials:
            return
        # The oid of the object we're looking at, starting at the root
        oid = ZERO
        # Start at the root, find all the objects the current revision of the
        # root references, and then for each of those, find all the objects it
        # references, and so on until we've traversed the entire object graph.
        while oid:
            if self._stop:
                raise PackStop, 'stopped in _mark()'
            if not self._packmark.has_key(oid):
                # We've haven't yet seen this object
                self._packmark.put(oid, PRESENT, txn=txn)
                # Get the pickle data for this object
                tid = self._getCurrentSerial(oid)
                # Say there's no root object (as is the case in some of the
                # unit tests), and we're looking up oid ZERO.  Then serial
                # will be None.
                if tid is not None:
                    data = self._pickles[oid+tid]
                    # Now get the oids of all the objects referenced by this
                    # pickle
                    refdoids = []
                    referencesf(data, refdoids)
                    # And append them to the queue for later
                    for oid in refdoids:
                        self._oidqueue.append(oid, txn)
            # Pop the next oid off the queue and do it all again
            rec = self._oidqueue.consume(txn)
            oid = rec and rec[1]
        assert len(self._oidqueue) == 0

    def _sweep(self, txn):
        c = self._serials.cursor(txn=txn)
        try:
            rec = c.first()
            while rec:
                if self._stop:
                    raise PackStop, 'stopped in _sweep()'
                oid = rec[0]
                rec = c.next()
                # If packmark (which knows about all the root reachable
                # objects) doesn't have a record for this guy, then we can zap
                # it.  Do so by appending to oidqueue.
                if not self._packmark.has_key(oid):
                    self._oidqueue.append(oid, txn)
        finally:
            c.close()
        # We're done with the mark table
        self._packmark.truncate(txn)

    def _collect_objs(self, txn):
        orec = self._oidqueue.consume(txn)
        while orec:
            if self._stop:
                raise PackStop, 'stopped in _collect_objs()'
            oid = orec[1]
            # Delete the object from the serials table
            c = self._serials.cursor(txn)
            try:
                try:
                    rec = c.set(oid)
                except db.DBNotFoundError:
                    rec = None
                while rec and rec[0] == oid:
                    if self._stop:
                        raise PackStop, 'stopped in _collect_objs() loop 1'
                    c.delete()
                    rec = c.next_dup()
                # We don't need the refcounts any more, but note that if the
                # object was never referenced from another object, there may
                # not be a refcounts entry.
                try:
                    self._refcounts.delete(oid, txn=txn)
                except db.DBNotFoundError:
                    pass
            finally:
                c.close()
            # Now collect the pickle data and do reference counting
            c = self._pickles.cursor(txn)
            try:
                try:
                    rec = c.set_range(oid)
                except db.DBNotFoundError:
                    rec = None
                while rec and rec[0][:8] == oid:
                    if self._stop:
                        raise PackStop, 'stopped in _collect_objs() loop 2'
                    data = rec[1]
                    c.delete()
                    rec = c.next()
                    deltas = {}
                    self._update(deltas, data, -1)
                    for oid, delta in deltas.items():
                        refcount = U64(self._refcounts.get(oid, ZERO)) + delta
                        if refcount <= 0:
                            self._oidqueue.append(oid, txn)
                        else:
                            self._refcounts.put(oid, p64(refcount), txn=txn)
            finally:
                c.close()
            # We really do want this down here, since _decrefPickle() could
            # add more items to the queue.
            orec = self._oidqueue.consume(txn)
        assert len(self._oidqueue) == 0

    #
    # Stuff we don't support
    #

    def supportsTransactionalUndo(self):
        return False

    def supportsUndo(self):
        return False

    def supportsVersions(self):
        return False

    # Don't implement these
    #
    # versionEmpty(self, version)
    # versions(self, max=None)
    # loadSerial(self, oid, serial)
    # getSerial(self, oid)
    # transactionalUndo(self, tid, transaction)
    # undoLog(self, first=0, last=-20, filter=None)
    # history(self, oid, version=None, size=1, filter=None)
    # iterator(self, start=None, stop=None)



class _Autopack(_WorkThread):
    NAME = 'autopacking'

    def _dowork(self):
        # Run the autopack phase
        self._storage.pack('ignored', referencesf)
