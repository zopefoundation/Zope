"""Berkeley storage with full undo and versioning support.

See Minimal.py for an implementation of Berkeley storage that does not support
undo or versioning.
"""

__version__ = '$Revision: 1.30 $'[-2:][0]

import sys
import struct
import time

# This uses the Dunn/Kuchling PyBSDDB v3 extension module available from
# http://pybsddb.sourceforge.net
from bsddb3 import db

from ZODB import POSException
from ZODB import utils
from ZODB.referencesf import referencesf
from ZODB.TimeStamp import TimeStamp
from ZODB.ConflictResolution import ConflictResolvingStorage, ResolvedSerial

# BerkeleyBase.BerkeleyBase class provides some common functionality for both
# the Full and Minimal implementations.  It in turn inherits from
# ZODB.BaseStorage.BaseStorage which itself provides some common storage
# functionality.
from BerkeleyBase import BerkeleyBase
from CommitLog import FullLog

# Flags for transaction status in the transaction metadata table.  You can
# only undo back to the last pack, and any transactions before the pack time
# get marked with the PROTECTED_TRANSACTION flag.  An attempt to undo past a
# PROTECTED_TRANSACTION will raise an POSException.UndoError.  By default,
# transactions are marked with the UNDOABLE_TRANSACTION status flag.
UNDOABLE_TRANSACTION = 'Y'
PROTECTED_TRANSACTION = 'N'

ZERO = '\0'*8
DNE = '\377'*8
# DEBUGGING
#DNE = 'nonexist'                                  # does not exist



class Full(BerkeleyBase, ConflictResolvingStorage):
    #
    # Overrides of base class methods
    #
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
        # pickles -- {(oid+revid) -> pickle}
        #     Maps the concrete object referenced by oid+revid to that
        #     object's data pickle.
        #
        # These are used only by the Full implementation.
        #
        # vids -- {version_string -> vid}
        #     Maps version strings (which are arbitrary) to vids.
        #
        # versions -- {vid -> version_string}
        #     Maps vids to version strings.
        #
        # currentVersions -- {vid -> [oid]}
        #     Maps vids to the oids of the objects modified in that version
        #     for all current versions (except the 0th version, which is the
        #     non-version).
        #
        # metadata -- {oid+revid -> vid+nvrevid+lrevid+previd}
        #     Maps oid+revid to object metadata.  This mapping is used to find
        #     other information about a particular concrete object revision.
        #     Essentially it stitches all the other pieces together.
        #
        #     vid is the version id for the concrete object revision, and will
        #     be zero if the object isn't living in a version.
        #
        #     nvrevid is the revision id pointing to the most current
        #     non-version concrete object revision.  So, if the object is
        #     living in a version and that version is aborted, the nvrevid
        #     points to the object revision that will soon be restored.
        #     nvrevid will be zero if the object was never modified in a
        #     version.
        #
        #     lrevid is the revision id pointing to object revision's pickle
        #     state (I think of it as the "live revision id" since it's the
        #     state that gives life to the concrete object described by this
        #     metadata record).
        #
        #     prevrevid is the revision id pointing to the previous state of
        #     the object.  This is used for undo.
        #
        # txnMetadata -- {tid -> status+userlen+desclen+user+desc+ext}
        #     Maps tids to metadata about a transaction.
        #
        #     Status is a 1-character status flag, which is used by the undo
        #     mechanism, and has the following values (see constants above):
        #         'N' -- This transaction is "pack protected".  You can only
        #                undo back to the last pack, and any transactions
        #                before the pack time get marked with this flag.
        #         'Y' -- It is okay to undo past this transaction.
        #
        #     userlen is the length in characters of the `user' field as an
        #         8-byte unsigned long integer
        #     desclen is the length in characters of the `desc' field as an
        #         8-byte unsigned long integer
        #     user is the user information passed to tpc_finish()
        #     desc is the description info passed to tpc_finish()
        #     ext is the extra info passed to tpc_finish().  It is a
        #         dictionary that we get already pickled by BaseStorage.
        #
        # txnoids -- {tid -> [oid]}
        #     Maps transaction ids to the oids of the objects modified by the
        #     transaction.
        #
        # refcounts -- {oid -> count}
        #     Maps objects to their reference counts.
        #
        # pickleRefcounts -- {oid+tid -> count}
        #     Maps the concrete object referenced by oid+tid to the reference
        #     count of its pickle.
        #
        # Tables common to the base framework 
        self._serials = self._setupDB('serials')
        self._pickles = self._setupDB('pickles')
        # These are specific to the full implementation
        self._vids            = self._setupDB('vids')
        self._versions        = self._setupDB('versions')
        self._currentVersions = self._setupDB('currentVersions', db.DB_DUP)
        self._metadata        = self._setupDB('metadata')
        self._txnMetadata     = self._setupDB('txnMetadata')
        self._txnoids         = self._setupDB('txnoids', db.DB_DUP)
        self._refcounts       = self._setupDB('refcounts')
        self._pickleRefcounts = self._setupDB('pickleRefcounts')
        # Initialize our cache of the next available version id.
        record = self._versions.cursor().last()
        if record:
            # Convert to a Python long integer.  Note that cursor.last()
            # returns key/value, and we want the key (which for the _version
            # table is is the vid).
            self.__nextvid = utils.U64(record[0])
        else:
            self.__nextvid = 0L
        # DEBUGGING
        #self._nextserial = 0L
        
    def close(self):
        if self._commitlog is not None:
            self._commitlog.close()
        self._serials.close()
        self._pickles.close()
        self._vids.close()
        self._versions.close()
        self._currentVersions.close()
        self._metadata.close()
        self._txnMetadata.close()
        self._txnoids.close()
        self._refcounts.close()
        self._pickleRefcounts.close()
        BerkeleyBase.close(self)

    def _begin(self, tid, u, d, e):
        # DEBUGGING
        #self._nextserial += 1
        #self._serial = utils.p64(self._nextserial)
        # Begin the current transaction.  Currently, this just makes sure that
        # the commit log is in the proper state.
        if self._commitlog is None:
            # JF: Chris was getting some weird errors / bizarre behavior from
            # Berkeley when using an existing directory or having non-BSDDB
            # files in that directory.
            self._commitlog = FullLog(dir=self._env.db_home)
        self._commitlog.start()

    def _finish(self, tid, u, d, e):
        # This is called from the storage interface's tpc_finish() method.
        # Its responsibilities are to finish the transaction with the
        # underlying database.
        #
        # We have a problem here because tpc_finish() is not supposed to raise
        # any exceptions.  However because finishing with the backend database
        # /can/ cause exceptions, they may be thrown from here as well.  If
        # that happens, we abort the transaction.
        #
        # Because of the locking semantics issue described above, finishing
        # the transaction in this case involves:
        #     - starting a transaction with Berkeley DB
        #     - replaying our commit log for object updates
        #     - storing those updates in BSDDB
        #     - committing those changes to BSDDB
        #
        # Once the changes are committed successfully to BSDDB, we're done
        # with our log file.
        #
        # tid is the transaction id
        # u is the user associated with the transaction
        # d is the description of the transaction
        # e is the transaction extension
        txn = self._env.txn_begin()
        try:
            # Update the transaction metadata
            userlen = len(u)
            desclen = len(d)
            lengths = struct.pack('>II', userlen, desclen)
            # BAW: it's slightly faster to use '%s%s%s%s%s' % ()
            # concatentation than string adds, but that will be dependent on
            # string length.  Those are both faster than using %c as first in
            # format string (even though we know the first one is a
            # character), and those are faster still than string.join().
            self._txnMetadata.put(tid,
                                  UNDOABLE_TRANSACTION + lengths + u + d + e,
                                  txn=txn)
            while 1:
                rec = self._commitlog.next()
                if rec is None:
                    break
                op, data = rec
                if op == 'o':
                    # This is a `versioned' object record.  Information about
                    # this object must be stored in the pickle table, the
                    # object metadata table, the currentVersions tables , and
                    # the transactions->oid table.
                    oid, vid, nvrevid, lrevid, pickle, prevrevid = data
                    key = oid + tid
                    if pickle:
                        # This was the result of a store() call which gives us
                        # a brand new pickle, so we need to update the pickles
                        # table.  The lrevid will be empty, and we make it the
                        # tid of this transaction
                        #
                        # Otherwise, this was the result of a commitVersion()
                        # or abortVersion() call, essentially moving the
                        # object to a new version.  We don't need to update
                        # the pickle table because we aren't creating a new
                        # pickle.
                        self._pickles.put(key, pickle, txn=txn)
                        lrevid = tid
                        # Boost the refcount of all the objects referred to by
                        # this pickle.  referencesf() scans a pickle and
                        # returns the list of objects referenced by the
                        # pickle.  BAW: the signature of referencesf() has
                        # changed for Zope 2.4, to make it more convenient to
                        # use.  Gotta stick with the backwards compatible
                        # version for now.
                        #
                        # FIXME: need to watch for two object revisions in the
                        # same transaction and only bump the refcount once,
                        # since we only keep the last of any such revisions.
                        refdoids = []
                        referencesf(pickle, refdoids)
                        for roid in refdoids:
                            refcount = self._refcounts.get(roid, ZERO, txn=txn)
                            refcount = utils.p64(utils.U64(refcount) + 1)
                            self._refcounts.put(roid, refcount, txn=txn)
                    # Update the metadata table
                    self._metadata.put(key, vid+nvrevid+lrevid+prevrevid,
                                       txn=txn)
                    # If we're in a real version, update this table too.  This
                    # ends up putting multiple copies of the vid/oid records
                    # in the table, but it's easier to weed those out later
                    # than to weed them out now.
                    if vid <> ZERO:
                        self._currentVersions.put(vid, oid, txn=txn)
                    self._serials.put(oid, tid, txn=txn)
                    self._txnoids.put(tid, oid, txn=txn)
                    # Update the pickle's reference count.  Remember, the
                    # refcount is stored as a string, so we have to do the
                    # string->long->string dance.
                    refcount = self._pickleRefcounts.get(key, ZERO, txn=txn)
                    refcount = utils.p64(utils.U64(refcount) + 1)
                    self._pickleRefcounts.put(key, refcount, txn=txn)
                elif op == 'v':
                    # This is a "create-a-version" record
                    version, vid = data
                    self._versions.put(vid, version, txn=txn)
                    self._vids.put(version, vid, txn=txn)
                elif op == 'd':
                    # This is a "delete-a-version" record
                    vid = data[0]
                    c = self._currentVersions.cursor(txn=txn)
                    try:
                        rec = c.set(vid)
                        while rec:
                            c.delete()
                            rec = c.next_dup()
                    finally:
                        c.close()
        except:
            # If any errors whatsoever occurred, abort the transaction with
            # Berkeley, leave the commit log file in the PROMISED state (since
            # its changes were never committed), and re-raise the exception.
            txn.abort()
            raise
        else:
            # Everything is hunky-dory.  Commit the Berkeley transaction, and
            # reset the commit log for the next transaction.
            txn.commit()
            self._closelog()

    #
    # Do some things in a version
    #

    def abortVersion(self, version, transaction):
        # Abort the version, but retain enough information to make the abort
        # undoable.
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        c = None                                  # the currentVersions cursor
        self._lock_acquire()
        try:
            # We can't abort the empty version, 'cause it ain't a version! :)
            if not version:
                raise POSException.VersionError
            # Let KeyErrors percolate up.  This is how we ensure that the
            # version we're aborting is not the empty string.
            vid = self._vids[version]
            # We need to keep track of the oids that are affected by the abort
            # so that we can return it to the connection, which must
            # invalidate the objects so they can be reloaded.  We use a set
            # here because currentVersions may have duplicate vid/oid records.
            oids = {}
            c = self._currentVersions.cursor()
            rec = c.set(vid)
            # Now cruise through all the records for this version, looking for
            # objects modified in this version, but which were not created in
            # this version.  For each of these objects, we're going to want to
            # write a log entry that will cause the non-version revision of
            # the object to become current.  This preserves the version
            # information for undo.
            while rec:
                oid = rec[1]                      # ignore the key
                rec = c.next_dup()
                if oids.has_key(oid):
                    # We've already dealt with this oid...
                    continue
                revid = self._serials[oid]
                meta = self._metadata[oid+revid]
                curvid, nvrevid = struct.unpack('>8s8s', meta[:16])
                # Make sure that the vid in the metadata record is the same as
                # the vid we sucked out of the vids table.
                if curvid <> vid:
                    raise POSException.StorageSystemError
                if nvrevid == ZERO:
                    # This object was created in the version, so we don't need
                    # to do anything about it.
                    continue
                # Get the non-version data for the object
                nvmeta = self._metadata[oid+nvrevid]
                curvid, nvrevid, lrevid = struct.unpack('>8s8s8s', nvmeta[:24])
                # We expect curvid to be zero because we just got the
                # non-version entry.
                if curvid <> ZERO:
                    raise POSException.StorageSystemError
                # Write the object id, live revision id, the current revision
                # id (which serves as the previous revid to this transaction)
                # to the commit log.
                self._commitlog.write_nonversion_object(oid, lrevid, revid)
                # Remember to return the oid...
                oids[oid] = 1
            # We've now processed all the objects on the discarded version, so
            # write this to the commit log and return the list of oids to
            # invalidate.
            self._commitlog.write_discard_version(vid)
            return oids.keys()
        finally:
            if c:
                c.close()
            self._lock_release()

    def commitVersion(self, src, dest, transaction):
        # Commit a source version `src' to a destination version `dest'.  It's
        # perfectly valid to move an object from one version to another.  src
        # and dest are version strings, and if we're committing to a
        # non-version, dest will be empty.
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        # Sanity checks
        if not src or src == dest:
            raise POSException.VersionCommitError

        c = None                                  # the currentVersions cursor
        self._lock_acquire()
        try:
            # Get the version ids associated with the source and destination
            # version strings.
            svid = self._vids[src]
            if not dest:
                dvid = ZERO
            else:
                # Find the vid for the destination version, or create one if
                # necessary.
                dvid = self.__findcreatevid(dest)
            # Keep track of the oids affected by this commit.  For why this is
            # a dictionary (really a set), see abortVersion() above.
            oids = {}
            c = self._currentVersions.cursor()
            rec = c.set(svid)
            # Now cruise through all the records for this version, writing to
            # the commit log all the objects changed in this version.
            while rec:
                oid = rec[1]                      # ignore the key
                rec = c.next_dup()
                if oids.has_key(oid):
                    continue
                revid = self._serials[oid]
                meta = self._metadata[oid+revid]
                curvid, nvrevid, lrevid = struct.unpack('>8s8s8s', meta[:24])
                # Our database better be consistent.
                if curvid <> svid:
                    raise POSException.StorageSystemError(
                        'oid: %s, moving from v%s to v%s, but lives in v%s' %
                        tuple(map(utils.U64, (oid, svid, dvid, curvid))))
                # If we're committing to a non-version, then the non-version
                # revision id ought to be zero also, regardless of what it was
                # for the source version.
                if not dest:
                    nvrevid = ZERO
                self._commitlog.write_moved_object(
                    oid, dvid, nvrevid, lrevid, revid)
                # Remember to return the oid...
                oids[oid] = 1
            # Now that we're done, we can discard this version
            self._commitlog.write_discard_version(svid)
            return oids.keys()
        finally:
            if c:
                c.close()
            self._lock_release()

    def modifiedInVersion(self, oid):
        # Return the version string of the version that contains the most
        # recent change to the object.  The empty string means the change
        # isn't in a version.
        self._lock_acquire()
        try:
            # Let KeyErrors percolate up
            revid = self._serials[oid]
            vid = self._metadata[oid+revid][:8]
            if vid == ZERO:
                # Not in a version
                return ''
            return self._versions[vid]
        finally:
            self._lock_release()

    #
    # Public storage interface
    #

    def load(self, oid, version):
        # BAW: in the face of application level conflict resolution, it's
        # /possible/ to load an object that is sitting in the commit log.
        # That's bogus though because there's no way to know what to return;
        # i.e. returning the not-yet-committed state isn't right (because you
        # don't know if the txn will be committed or aborted), and returning
        # the last committed state doesn't help.  So, don't do this!
        #
        # The solution is, in the Connection object wait to reload the object
        # until the transaction has been committed.  Still, we don't check for
        # this condition, although maybe we should.
        self._lock_acquire()
        try:
            # Get the current revid for the object.  As per the protocol, let
            # any KeyErrors percolate up.
            revid = self._serials[oid]
            # Get the metadata associated with this revision of the object.
            # All we really need is the vid, the non-version revid and the
            # pickle pointer revid.
            rec = self._metadata[oid+revid]
            vid, nvrevid, lrevid = struct.unpack('>8s8s8s', rec[:24])
            if lrevid == DNE:
                raise KeyError, 'Object does not exist'
            # If the object isn't living in a version, or if the version the
            # object is living in is the one that was requested, we simply
            # return the current revision's pickle.
            if vid == ZERO or self._versions.get(vid) == version:
                return self._pickles[oid+lrevid], revid
            # The object was living in a version, but not the one requested.
            # Semantics here are to return the non-version revision.
            lrevid = self._metadata[oid+nvrevid][16:24]
            return self._pickles[oid+lrevid], nvrevid
        finally:
            self._lock_release()

    def _loadSerialEx(self, oid, serial):
        # Just like loadSerial, except that it returns both the pickle and the
        # version this object revision is living in.
        self._lock_acquire()
        try:
            # Get the pointer to the pickle (i.e. live revid, or lrevid)
            # corresponding to the oid and the supplied serial
            # a.k.a. revision.
            vid, ign, lrevid = struct.unpack(
                '>8s8s8s', self._metadata[oid+serial][:24])
            if vid == ZERO:
                version = ''
            else:
                version = self._versions[vid]
            return self._pickles[oid+lrevid], version
        finally:
            self._lock_release()

    def loadSerial(self, oid, serial):
        return self._loadSerialEx(oid, serial)[0]
                        
    def __findcreatevid(self, version):
        # Get the vid associated with a version string, or create one if there
        # is no vid for the version.
        #
        # First we look for the version in the Berkeley table.  If not
        # present, then we look in the commit log to see if a new version
        # creation is pending.  If still missing, then create the new version
        # and add it to the commit log.
        vid = self._vids.get(version)
        if vid is None:
            vid = self._commitlog.get_vid(version)
        if vid is None:
            self.__nextvid = self.__nextvid + 1
            # Convert the int/long version ID into an 8-byte string
            vid = utils.p64(self.__nextvid)
            self._commitlog.write_new_version(version, vid)
        return vid

    def store(self, oid, serial, data, version, transaction):
        # Transaction equivalence guard
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        conflictresolved = 0
        self._lock_acquire()
        try:
            # Check for conflict errors.  JF says: under some circumstances,
            # it is possible that we'll get two stores for the same object in
            # a single transaction.  It's not clear though under what
            # situations that can occur or what the semantics ought to be.
            # For now, we'll assume this doesn't happen.
            oserial = orevid = self._serials.get(oid)
            if oserial is None:
                # There's never been a previous revision of this object, so
                # set its non-version revid to zero.
                nvrevid = ZERO
                oserial = ZERO
            elif serial <> oserial:
                # The object exists in the database, but the serial number
                # given in the call is not the same as the last stored serial
                # number.  First, attempt application level conflict
                # resolution, and if that fails, raise a ConflictError.
                data = self.tryToResolveConflict(oid, oserial, serial, data)
                if data:
                    conflictresolved = 1
                else:
                    raise POSException.ConflictError(
                        'serial number mismatch (was: %s, has: %s)' %
                        (utils.U64(oserial), utils.U64(serial)))
            # Do we already know about this version?  If not, we need to
            # record the fact that a new version is being created.  `version'
            # will be the empty string when the transaction is storing on the
            # non-version revision of the object.
            if version:
                vid = self.__findcreatevid(version)
            else:
                # vid 0 means no explicit version
                vid = ZERO
                nvrevid = ZERO
            # A VersionLockError occurs when a particular object is being
            # stored on a version different than the last version it was
            # previously stored on (as long as the previous version wasn't
            # zero, of course).
            #
            # Get the old version, which only makes sense if there was a
            # previously stored revision of the object.
            if orevid:
                rec = self._metadata[oid+orevid]
                ovid, onvrevid = struct.unpack('>8s8s', rec[:16])
                if ovid == ZERO:
                    # The old revision's vid was zero any version is okay.
                    # But if we're storing this on a version, then the
                    # non-version revid will be the previous revid for the
                    # object.
                    if version:
                        nvrevid = orevid
                elif ovid <> vid:
                    # The old revision was on a version different than the
                    # current version.  That's a no no.
                    raise POSException.VersionLockError(
                        'version mismatch for object %s (was: %s, got: %s)' %
                        tuple(map(utils.U64, (oid, ovid, vid))))
                else:
                    nvrevid = onvrevid
            # Record the update to this object in the commit log.
            self._commitlog.write_object(oid, vid, nvrevid, data, oserial)
        finally:
            self._lock_release()
        # Return our cached serial number for the object.  If conflict
        # resolution occurred, we return the special marker value.
        if conflictresolved:
            return ResolvedSerial
        return self._serial

    def transactionalUndo(self, tid, transaction):
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        newrevs = []
        newstates = []
        c = None
        self._lock_acquire()
        try:
            # First, make sure the transaction isn't protected by a pack.
            status = self._txnMetadata[tid][0]
            if status <> UNDOABLE_TRANSACTION:
                raise POSException.UndoError, 'Transaction cannot be undone'

            # Calculate all the oids modified in the transaction
            c = self._txnoids.cursor()
            rec = c.set(tid)
            while rec:
                oid = rec[1]                      # ignore the key
                rec = c.next_dup()
                # In order to be able to undo this transaction, we must be
                # undoing either the current revision of the object, or we
                # must be restoring the exact same pickle (identity compared)
                # that would be restored if we were undoing the current
                # revision.  Otherwise, we attempt application level conflict
                # resolution.  If that fails, we raise an exception.
                revid = self._serials[oid]
                if revid == tid:
                    vid, nvrevid, lrevid, prevrevid = struct.unpack(
                        '>8s8s8s8s', self._metadata[oid+tid])
                    # We can always undo the last transaction.  The prevrevid
                    # pointer doesn't necessarily point to the previous
                    # transaction, if the revision we're undoing was itself an
                    # undo.  Use a cursor to find the previous revision of
                    # this object.
                    mdc = self._metadata.cursor()
                    try:
                        mdc.set(oid+revid)
                        mrec = mdc.prev()
                        # If we're undoing the first record, either for the
                        # whole system or for this object, just write a
                        # zombification record
                        if not mrec or mrec[0][:8] <> oid:
                            newrevs.append((oid, vid+nvrevid+DNE+revid))
                        # BAW: If the revid of this object record is the same
                        # as the revid we're being asked to undo, then I think
                        # we have a problem (since the storage invariant is
                        # that it doesn't retain metadata records for multiple
                        # modifications of the object in the same txn).
                        elif mrec[0][8:] == revid:
                            raise StorageSystemError
                        # All is good, so just restore this metadata record
                        else:
                            newrevs.append((oid, mrec[1]))
                    finally:
                        mdc.close()
                else:
                    # We need to compare the lrevid (pickle pointers) of the
                    # transaction previous to the current one, and the
                    # transaction previous to the one we want to undo.  If
                    # their lrevids are the same, it's undoable.
                    last_prevrevid = self._metadata[oid+revid][24:]
                    target_prevrevid = self._metadata[oid+tid][24:]
                    if target_prevrevid == last_prevrevid == ZERO:
                        # We're undoing the object's creation, so the only
                        # thing to undo from there is the zombification of the
                        # object, i.e. the last transaction for this object.
                        vid, nvrevid = struct.unpack(
                            '>8s8s', self._metadata[oid+tid][:16])
                        newrevs.append((oid, vid+nvrevid+DNE+revid))
                        continue
                    elif target_prevrevid == ZERO or last_prevrevid == ZERO:
                        # The object's revision is in it's initial creation
                        # state but we're asking for an undo of something
                        # other than the initial creation state.  No, no.
                        raise POSException.UndoError, 'Undoing mismatch'
                    last_lrevid     = self._metadata[oid+last_prevrevid][16:24]
                    target_metadata = self._metadata[oid+target_prevrevid]
                    target_lrevid   = target_metadata[16:24]
                    # If the pickle pointers of the object's last revision
                    # and the undo-target revision are the same, then the
                    # transaction can be undone.  Note that we take a short
                    # cut here, since we really want to test pickle equality,
                    # but this is good enough for now.
                    if target_lrevid == last_lrevid:
                        newrevs.append((oid, target_metadata))
                    # They weren't equal, but let's see if there are undos
                    # waiting to be committed.
                    elif target_lrevid == self._commitlog.get_prevrevid(oid):
                        newrevs.append((oid, target_metadata))
                    else:
                        # Attempt application level conflict resolution
                        data = self.tryToResolveConflict(
                            oid, revid, tid, self._pickles[oid+target_lrevid])
                        if data:
                            # The problem is that the `data' pickle probably
                            # isn't in the _pickles table, and even if it
                            # were, we don't know what the lrevid pointer to
                            # it would be.  This means we need to do a
                            # write_object() not a write_object_undo().
                            vid, nvrevid, lrevid, prevrevid = struct.unpack(
                                '>8s8s8s8s', target_metadata)
                            newstates.append((oid, vid, nvrevid, data,
                                              prevrevid))
                        else:
                            raise POSException.UndoError(
                                'Cannot undo transaction')
            # Okay, we've checked all the objects affected by the transaction
            # we're about to undo, and everything looks good.  So now we'll
            # write to the log the new object records we intend to commit.
            oids = {}
            for oid, metadata in newrevs:
                vid, nvrevid, lrevid, prevrevid = struct.unpack(
                    '>8s8s8s8s', metadata)
                self._commitlog.write_object_undo(oid, vid, nvrevid, lrevid,
                                                  prevrevid)
                # We're slightly inefficent here: if we make two undos to the
                # same object during the same transaction, we'll write two
                # records to the commit log.  This works because the last one
                # will always overwrite previous ones, but it also means we'll
                # see duplicate oids in this iteration.
                oids[oid] = 1
            for oid, vid, nvrevid, data, prevrevid in newstates:
                self._commitlog.write_object(oid, vid, nvrevid, data,
                                             prevrevid)
                oids[oid] = 1
            return oids.keys()
        finally:
            if c:
                c.close()
            self._lock_release()

    def undoLog(self, first=0, last=-20, filter=None):
        # Get a list of transaction ids that can be undone, based on the
        # determination of the filter.  filter is a function which takes a
        # transaction description and returns true or false.
        #
        # Note that this method has been deprecated by undoInfo() which itself
        # has some flaws, but is the best we have now.  We don't actually need
        # to implement undoInfo() because BaseStorage (which we eventually
        # inherit from) mixes in the UndoLogCompatible class which provides an
        # implementation written in terms of undoLog().
        #
        # Interface specifies that if last is < 0, its absolute value is the
        # maximum number of transactions to return.
        if last < 0:
            last = abs(last)
        c = None                                  # tnxMetadata cursor
        txnDescriptions = []                      # the return value
        i = 0                                     # first <= i < last
        self._lock_acquire()
        try:
            c = self._txnMetadata.cursor()
            # We start at the last transaction and scan backwards because we
            # can stop early if we find a transaction that is earlier than a
            # pack.  We still have the potential to scan through all the
            # transactions.
            rec = c.last()
            while rec and i < last:
                tid, data = rec
                rec = c.prev()
                status = data[0]
                if status == PROTECTED_TRANSACTION:
                    break
                userlen, desclen = struct.unpack('>II', data[1:9])
                user = data[9:9+userlen]
                desc = data[9+userlen:9+userlen+desclen]
                ext = data[9+userlen+desclen:]
                # Create a dictionary for the TransactionDescription
                txndesc = {'id'         : tid,
                           'time'       : TimeStamp(tid).timeTime(),
                           'user_name'  : user,
                           'description': desc,
                           }
                # The extension stuff is a picklable mapping, so if we can
                # unpickle it, we update the TransactionDescription dictionary
                # with that data.  BAW: The bare except is moderately
                # disgusting, but I'm too lazy to figure out what exceptions
                # could actually be raised here...
                if ext:
                    try:
                        txndesc.update(pickle.loads(ext))
                    except:
                        pass
                # Now call the filter to see if this transaction should be
                # added to the return list...
                if filter is None or filter(txndesc):
                    # ...and see if this is within the requested ordinals
                    if i >= first:
                        txnDescriptions.append(txndesc)
                    i = i + 1
            return txnDescriptions
        finally:
            if c:
                c.close()
            self._lock_release()

    def versionEmpty(self, version):
        # Return true if version is empty.
        self._lock_acquire()
        try:
            # First, check if we're querying the empty (i.e. non) version
            if not version:
                c = self._serials.cursor()
                try:
                    rec = c.first()
                    return not rec
                finally:
                    c.close()
            # If the named version doesn't exist or there are no objects in
            # the version, then return true.
            missing = []
            vid = self._vids.get(version, missing)
            if vid is missing:
                return 1
            if self._currentVersions.has_key(vid):
                return 0
            else:
                return 1
        finally:
            self._lock_release()

    def versions(self, max=None):
        # Return the list of current versions, as strings, up to the maximum
        # requested.
        self._lock_acquire()
        c = None
        try:
            c = self._currentVersions.cursor()
            rec = c.first()
            retval = []
            while rec and (max is None or max > 0):
                # currentVersions maps vids to [oid]'s so dig the key out of
                # the returned record and look the vid up in the
                # vids->versions table.
                retval.append(self._versions[rec[0]])
                # Since currentVersions has duplicates (i.e. multiple vid keys
                # with different oids), get the next record that has a
                # different key than the current one.
                rec = c.next_nodup()
                if max is not None:
                    max = max - 1
            return retval
        finally:
            if c:
                c.close()
            self._lock_release()

    def history(self, oid, version=None, size=1, filter=None):
        self._lock_acquire()
        try:
            # Jim says:
            #
            #     This documentation is wrong. I think that the version should
            #     be ignored.  It really shouldn't be in the signature. Zope
            #     never passes the version argument.
            #
            # so we ignore `version', which makes our lives a bit easier.  We
            # start with the most recent revision of the object, then search
            # the transaction records backwards until we find enough records.
            history = []
            revid = self._serials[oid]
            # BAW: Again, let KeyErrors percolate up
            while len(history) < size:
                # Some information comes out of the revision metadata...
                vid, nvrevid, lrevid, previd = struct.unpack(
                    '>8s8s8s8s', self._metadata[oid+revid])
                # ...while other information comes out of the transaction
                # metadata.
                txnmeta = self._txnMetadata[revid]
                userlen, desclen = struct.unpack('>II', txnmeta[1:9])
                user = txnmeta[9:9+userlen]
                desc = txnmeta[9+userlen:9+userlen+desclen]
                # Now get the pickle size
                data = self._pickles[oid+lrevid]
                # Create a HistoryEntry structure, which turns out to be a
                # dictionary with some specifically named entries (BAW:
                # although this poorly documented).
                if vid == ZERO:
                    retvers = ''
                else:
                    retvers = self._versions[vid]
                # The HistoryEntry object
                d = {'time'       : TimeStamp(revid).timeTime(),
                     'user_name'  : user,
                     'description': desc,
                     'serial'     : revid,
                     'version'    : retvers,
                     'size'       : len(data),
                     }
                if filter is None or filter(d):
                    history.append(d)
                # Chase the link backwards to the next most historical
                # revision, stopping when we've reached the end.
                if previd == ZERO:
                    break
                revid = previd
            return history
        finally:
            self._lock_release()

    def _zapobject(self, oid, referencesf):
        # Delete all records referenced by this object
        self._serials.delete(oid)
        self._refcounts.delete(oid)
        # Run through all the metadata records associated with this object,
        # and recursively zap all its revisions.  Keep track of the tids and
        # vids referenced by the metadata record, so that we can clean up the
        # txnoids and currentVersions tables.
        tids = {}
        vids = {}
        c = self._metadata.cursor()
        try:
            try:
                rec = c.set_range(oid)
            except db.DBNotFoundError:
                return
            while rec and rec[0][:8] == oid:
                key, data = rec
                rec = c.next()
                tid = key[8:]
                tids[tid] = 1
                vid = data[:8]
                if vid <> ZERO:
                    vids[vid] = 1
                self._zaprevision(key, referencesf)
        finally:
            c.close()
        # Zap all the txnoid records...
        c = self._txnoids.cursor()
        try:
            for tid in tids.keys():
                rec = c.set_both(tid, oid)
                while rec:
                    k, v = rec
                    if k <> tid or v <> oid:
                        break
                    c.delete()
                    rec = c.next()
        finally:
            c.close()
        # ...and all the currentVersion records...
        c = self._currentVersions.cursor()
        try:
            for vid in vids.keys():
                rec = c.set_both(vid, oid)
                while rec:
                    k, v = rec
                    if k <> vid or v <> oid:
                        break
                    c.delete()
                    rec = c.next()
        finally:
            c.close()
        # ... now for each vid, delete the versions->vid and vid->versions
        # mapping if we've deleted all references to this vid
        for vid in vids.keys():
            if self._currentVersions.get(vid):
                continue
            version = self._versions[vid]
            self._versions.delete(vid)
            self._vids.delete(version)

    def _zaprevision(self, key, referencesf):
        # Delete the metadata record pointed to by the key, decrefing the
        # reference counts of the pickle pointed to by this record, and
        # perform cascading decrefs on the referenced objects.
        #
        # We need the lrevid which points to the pickle for this revision.
        try:
            lrevid = self._metadata[key][16:24]
        except KeyError:
            return
        # Decref the reference count of the pickle pointed to by oid+lrevid.
        # If the reference count goes to zero, we can garbage collect the
        # pickle, and decref all the objects pointed to by the pickle (with of
        # course, cascading garbage collection).
        pkey = key[:8] + lrevid
        refcount = utils.U64(self._pickleRefcounts[pkey]) - 1
        if refcount > 0:
            self._pickleRefcounts.put(pkey, utils.p64(refcount))
        else:
            # The refcount of this pickle has gone to zero, so we need to
            # garbage collect it, and decref all the objects it points to.
            pickle = self._pickles[pkey]
            # Sniff the pickle to get the objects it refers to
            refoids = []
            referencesf(pickle, refoids)
            # Now decref the reference counts for each of those objects.  If
            # the object's refcount goes to zero, remember the oid so we can
            # recursively zap its metadata records too.
            collectables = {}
            for oid in refoids:
                refcount = utils.U64(self._refcounts[oid]) - 1
                if refcount > 0:
                    self._refcounts.put(oid, utils.p64(refcount))
                else:
                    collectables[oid] = 1
            # Garbage collect all objects with refcounts that just went to
            # zero.
            for oid in collectables.keys():
                self._zapobject(oid, referencesf)
            # We can now delete both the pickleRefcounts and pickle entry for
            # this garbage collected pickle.
            self._pickles.delete(pkey)
            self._pickleRefcounts.delete(pkey)
        # We can now delete this metadata record.
        self._metadata.delete(key)

    def pack(self, t, referencesf):
        # BAW: This doesn't play nicely if you enable the `debugging revids'
        #
        # t is a TimeTime, or time float, convert this to a TimeStamp object,
        # using an algorithm similar to what's used in FileStorage.  The
        # TimeStamp can then be used as a key in the txnMetadata table, since
        # we know our revision id's are actually TimeStamps.
        t0 = TimeStamp(*(time.gmtime(t)[:5] + (t%60,)))
        self._lock_acquire()
        c = None
        tidmarks = {}
        oids = {}
        try:    
            # Figure out when to pack to.  We happen to know that our
            # transaction ids are really timestamps.
            c = self._txnoids.cursor()
            # Need to use the repr of the TimeStamp so we get a string
            try:
                rec = c.set_range(`t0`)
            except db.DBNotFoundError:
                rec = c.last()
            while rec:
                tid, oid = rec
                rec = c.prev()
                # We need to mark this transaction as having participated in a
                # pack, so that undo will not create a temporal anomaly.
                if not tidmarks.has_key(tid):
                    meta = self._txnMetadata[tid]
                    # Has this transaction already been packed?  If so, we can
                    # stop here... I think!
                    if meta[0] == PROTECTED_TRANSACTION:
                        break
                    self._txnMetadata[tid] = PROTECTED_TRANSACTION + meta[1:]
                    tidmarks[tid] = 1
                # For now, just remember which objects are touched by the
                # packable
                if oid <> ZERO:
                    oids[oid] = 1
            # Now look at every object revision metadata record for the
            # objects that have been touched in the packable transactions.  If
            # the metadata record points at the current revision of the
            # object, ignore it, otherwise reclaim it.
            c.close()
            c = self._metadata.cursor()
            for oid in oids.keys():
                try:
                    current = self._serials[oid]
                except KeyError:
                    continue
                try:
                    rec = c.set_range(oid)
                except db.DBNotFoundError:
                    continue
                while rec:
                    key, data = rec
                    rec = c.next()
                    if key[:8] <> oid:
                        break
                    if key[8:] == current:
                        continue
                    self._zaprevision(key, referencesf)
                # Now look and see if the object has a reference count of
                # zero, and if so garbage collect it.
                refcounts = self._refcounts.get(oid)
                if not refcounts:
                    # The current revision should be the only revision of this
                    # object that exists, otherwise its refcounts shouldn't be
                    # zero.
                    self._zaprevision(oid+current, referencesf)
                    # And delete a few other records that _zaprevisions()
                    # doesn't clean up
                    self._serials.delete(oid)
                    if refcounts <> None:
                        self._refcounts.delete(oid)
        finally:
            if c:
                c.close()
            self._lock_release()

    # GCable interface, for cyclic garbage collection
    #
    # BAW: Note that the GCable interface methods are largely untested.
    # Support for these is off the table for the 1.0 release of the Berkeley
    # storage.
    def gcTrash(oids):
        """Given a list of oids, treat them as trash.

        This means they can be garbage collected, with all necessary cascading
        reference counting performed
        """
        # BAW: this is broken -- make it look like the end of pack()
        self._lock_acquire()
        c = None
        try:
            c = self._metadata.cursor()
            for oid in oids:
                # Convert to a string
                oid = utils.p64(oid)
                # Delete all the metadata records
                rec = c.set(oid)
                while rec:
                    key, data = rec
                    rec = c.next_dup()
                    self._zaprevision(key)
        finally:
            if c:
                c.close()
            self._lock_release()

    def gcRefcount(oid):
        """Return the reference count of the specified object.
        
        Raises KeyError if there is no object with oid.  Both the oid argument
        and the returned reference count are integers.
        """
        self._lock_acquire()
        try:
            return utils.U64(self._refcounts[utils.p64(oid)])
        finally:
            self._lock_release()

    def gcReferences(oid):
        """Return a list of oids that the specified object refers to.

        Raises KeyError if there is no object with oid.  The oid argument
        is an integer; the return value is a list of integers of oids.
        """
        oids = []
        c = None
        self._lock_acquire()
        try:
            c = self._pickles.cursor()
            rec = c.set(utils.p64(oid))
            while rec:
                # We don't care about the key
                pickle = rec[1]
                rec = c.next_dup()
                # Sniff the pickle for object references
                tmpoids = []
                referencesf(pickle, tmpoids)
                # Convert to unsigned longs
                oids.extend(map(utils.U64, tmpoids))
                # Make sure there's no duplicates, and convert to int
            return oids
        finally:
            if c:
                c.close()
            self._lock_release()

    # Fail-safe `iterator' interface, used to copy and analyze storage
    # transaction data.
    def iterator(self):
        """Get a transactions iterator for the storage."""
        return _TransactionsIterator(self)

    def _nexttxn(self, tid):
        self._lock_acquire()
        c = self._txnMetadata.cursor()
        try:
            # Berkeley raises DBNotFound exceptions (a.k.a. KeyError) to
            # signal that it's at the end of records.  Turn these into
            # IndexError to signal the end of iteration.
            try:
                if tid is None:
                    # We want the first transaction
                    rec = c.first()
                else:
                    # Get the next transaction after the specified one.
                    c.set(tid)
                    rec = c.next()
            except KeyError:
                raise IndexError
            if rec is None:
                raise IndexError
            tid, data = rec
            # Now unpack the necessary information.  Don't impedence match the
            # status flag (that's done by the caller).
            status = data[0]
            userlen, desclen = struct.unpack('>II', data[1:9])
            user = data[9:9+userlen]
            desc = data[9+userlen:9+userlen+desclen]
            ext = data[9+userlen+desclen:]
            return tid, status, user, desc, ext
        finally:
            if c:
                c.close()
            self._lock_release()

    def _alltxnoids(self, tid):
        self._lock_acquire()
        c = self._txnoids.cursor()
        try:
            oids = []
            oidkeys = {}
            rec = c.set(tid)
            while rec:
                # Ignore the key
                oid = rec[1]
                if not oidkeys.has_key(oid):
                    oids.append(oid)
                    oidkeys[oid] = 1
                rec = c.next_dup()
            return oids
        finally:
            c.close()
            self._lock_release()

    # Other interface assertions
    def supportsTransactionalUndo(self):
        return 1

    def supportsUndo(self):
        return 1

    def supportsVersions(self):
        return 1



class _TransactionsIterator:
    """Provide forward iteration through the transactions in a storage.

    Transactions *must* be accessed sequentially (e.g. with a for loop).
    """
    def __init__(self, storage):
        self._storage = storage
        self._tid = None

    def __getitem__(self, i):
        """Return the ith item in the sequence of transaction data.

        Items must be accessed sequentially, and are instances of
        RecordsIterator.  An IndexError will be raised after all of the items
        have been returned.
        """
        # Let IndexErrors percolate up.
        tid, status, user, desc, ext = self._storage._nexttxn(self._tid)
        self._tid = tid
        return _RecordsIterator(self._storage, tid, status, user, desc, ext)



class _RecordsIterator:
    """Provide transaction meta-data and forward iteration through the
    transactions in a storage.
    
    Items *must* be accessed sequentially (e.g. with a for loop).
    """

    # Transaction id as an 8-byte timestamp string
    tid = None

    # Transaction status code;
    #   ' ' -- normal
    #   'p' -- Transaction has been packed, and contains incomplete data.
    #
    # Note that undone ('u') and checkpoint transactions ('c') should not be
    # included.
    status = None

    # The standard transaction metadata
    user = None
    description = None
    _extension = None

    def __init__(self, storage, tid, status, user, desc, ext):
        self._storage = storage
        self.tid = tid
        # Impedence matching
        if status == UNDOABLE_TRANSACTION:
            self.status = ' '
        else:
            self.status = 'p'
        self.user = user
        self.description = desc
        self._extension = ext
        # Internal pointer
        self._oids = self._storage._alltxnoids(self.tid)
        # To make .pop() more efficient
        self._oids.reverse()

    def __getitem__(self, i):
        """Return the ith item in the sequence of record data.

        Items must be accessed sequentially, and are instances of Record.  An
        IndexError will be raised after all of the items have been
        returned.
        """
        # Let IndexError percolate up
        oid = self._oids.pop()
        pickle, version = self._storage._loadSerialEx(oid, self.tid)
        return _Record(oid, self.tid, version, pickle)



class _Record:
    # Object Id
    oid = None
    # Object serial number (i.e. revision id)
    serial = None
    # Version string
    version = None
    # Data pickle
    data = None

    def __init__(self, oid, serial, version, data):
        self.oid = oid
        self.serial = serial
        self.version = version
        self.data = data
