"""Berkeley storage with full undo and versioning support.

See Minimal.py for an implementation of Berkeley storage that does not support
undo or versioning.
"""

# $Revision: 1.9 $
__version__ = '0.1'

import struct

# This uses the Dunn/Kuchling PyBSDDB v3 extension module available from
# http://pybsddb.sourceforge.net
from bsddb3 import db

from ZODB import POSException
from ZODB import utils
from ZODB.referencesf import referencesf
from ZODB import TimeStamp

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

zero = '\0'*8



class InternalInconsistencyError(POSException.POSError, AssertionError):
    """Raised when we detect an internal inconsistency in our tables."""



class Full(BerkeleyBase):
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
            self.__nextvid = utils.U64(vid[0])
        else:
            self.__nextvid = 0L
        
    def close(self):
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
        # Begin the current transaction.  Currently, this just makes sure that
        # the commit log is in the proper state.
        if self._commitlog is None:
            # JF: Chris was getting some weird errors / bizarre behavior from
            # Berkeley when using an existing directory or having non-BSDDB
            # files in that directory.
            self._commitlog = FullLog(dir=self._env.db_home)
        self._commitlog.start()

    def _vote(self, transaction):
        # From here on out, we promise to commit all the registered changes,
        # so rewind and put our commit log in the PROMISED state.
        self._commitlog.promise()

    def _finish(self, tid, u, d, e):
        global zero
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
                        refdoids = []
                        referencesf(pickle, refdoids)
                        for roid in refdoids:
                            refcount = self._refcounts.get(roid, zero, txn=txn)
                            refcount = utils.p64(utils.U64(refcount) + 1)
                            self._refcounts.put(roid, refcount, txn=txn)
                    # Update the metadata table
                    self._metadata.put(key, vid+nvrevid+lrevid+prevrevid,
                                       txn=txn)
                    # If we're in a real version, update this table too.  This
                    # ends up putting multiple copies of the vid/oid records
                    # in the table, but it's easier to weed those out later
                    # than to weed them out now.
                    if vid <> zero:
                        self._currentVersions.put(vid, oid, txn=txn)
                    self._serials.put(oid, tid, txn=txn)
                    self._txnoids.put(tid, oid, txn=txn)
                    # Update the pickle's reference count.  Remember, the
                    # refcount is stored as a string, so we have to do the
                    # string->long->string dance.
                    refcount = self._pickleRefcounts.get(key, zero, txn=txn)
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
                            rec = c.next()
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
        global zero
        # Abort the version, but retain enough information to make the abort
        # undoable.
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        c = None                                  # the currentVersions cursor
        self._lock_acquire()
        try:
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
                rec = c.next()
                if oids.has_key(oid):
                    # We've already dealt with this oid...
                    continue
                revid = self._serials[oid]
                meta = self._metadata[oid+revid]
                curvid, nvrevid = struct.unpack('8s8s', meta[:16])
                # Make sure that the vid in the metadata record is the same as
                # the vid we sucked out of the vids table.
                if curvid <> vid:
                    raise POSException.VersionError(
                        'aborting a non-current version')
                if nvrevid == zero:
                    # This object was created in the version, so we don't need
                    # to do anything about it.
                    continue
                # Get the non-version data for the object
                nvmeta = self._metadata[oid+nvrevid]
                curvid, nvrevid, lrevid = struct.unpack('8s8s8s', nvmeta[:24])
                # We expect curvid to be zero because we just got the
                # non-version entry.
                if curvid <> zero:
                    raise InternalInconsistencyError
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
        global zero
        # Commit a source version `src' to a destination version `dest'.  It's
        # perfectly valid to move an object from one version to another.  src
        # and dest are version strings, and if we're committing to a
        # non-version, dest will be empty.
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        c = None                                  # the currentVersions cursor
        self._lock_acquire()
        try:
            # The transaction id for this commit
            tid = self._serial
            # Get the version ids associated with the source and destination
            # version strings.
            svid = self._vids[src]
            if not dest:
                dvid = zero
            else:
                # Find the vid for the destination version, or create one if
                # necessary.
                dvid = self.__findcreatevid(dest)
            # Keep track of the oids affected by this commit.
            oids = []
            c = self._currentVersions.cursor()
            rec = c.set(vid)
            # Now cruise through all the records for this version, writing to
            # the commit log all the objects changed in this version.
            while rec:
                oid = rec[1]                      # ignore the key
                revid = self._serials[oid]
                meta = self._metadata[oid+revid]
                curvid, nvrevid, lrevid = struct.unpack('8s8s8s', meta[:24])
                # Our database better be consistent.
                if curvid <> svid:
                    raise InternalInconsistencyError
                # If we're committing to a non-version, then the non-version
                # revision id ought to be zero also, regardless of what it was
                # for the source version.
                if not dest:
                    nvrevid = zero
                self._commitlog.write_moved_object(
                    oid, dvid, nvrevid, lrevid, tid)
                # Remember to return the oid...
                oids.append(oid)
                # ...and get the next record for this vid
                rec = c.next()
            # Now that we're done, we can discard this version
            self._commitlog.write_discard_version(vid)
            return oids
        finally:
            if c:
                c.close()
            self._lock_release()

    def modifiedInVersion(self, oid):
        global zero
        # Return the version string of the version that contains the most
        # recent change to the object.  The empty string means the change
        # isn't in a version.
        self._lock_acquire()
        try:
            # Let KeyErrors percolate up
            revid = self._serials[oid]
            vid = self._metadata[oid+revid][:8]
            if vid == zero:
                # Not in a version
                return ''
            return self._versions[vid]
        finally:
            self._lock_release()

    #
    # Public storage interface
    #

    def load(self, oid, version):
        global zero
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
            # If the object isn't living in a version, or if the version the
            # object is living in is equal to the version that's being
            # requested, then we can simply return the pickle referenced by
            # the revid.
            if vid == zero or self._versions[vid] == version:
                return self._pickles[oid+lrevid], revid
            # Otherwise, we recognize that an object cannot be stored in more
            # than one version at a time (although this may change if/when
            # "Unlocked" versions are added).  So we return the non-version
            # revision of the object.  Make sure the version is empty though.
            if version:
                raise POSException.VersionError(
                    'Undefined version: %s' % version)
            lrevid = self._metadata[oid+nvrevid][16:24]
            return self._pickles[oid+lrevid], nvrevid
        finally:
            self._lock_release()

    def loadSerial(self, oid, serial):
        # Return the revision of the object with the given serial number.
        self._lock_acquire()
        try:
            # Get the pointer to the pickle (i.e. live revid, or lrevid)
            # corresponding to the oid and the supplied serial
            # a.k.a. revision.
            lrevid = self._metadata[oid+serial][16:24]
            return self._pickles[oid+lrevid]
        finally:
            self._lock_release()
                        
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
        global zero

        # Transaction equivalence guard
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

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
                nvrevid = zero
                oserial = zero
            elif serial <> oserial:
                # The object exists in the database, but the serial number
                # given in the call is not the same as the last stored serial
                # number.  Raise a ConflictError.
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
                vid = zero
                nvrevid = zero
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
                if ovid == zero:
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
        # Return our cached serial number for the object.
        return self._serial

    def transactionalUndo(self, tid, transaction):
        # FIXME: what if we undo an abortVersion or commitVersion, don't we
        # need to re-populate the currentVersions table?
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        newrevs = []
        c = None
        self._lock_acquire()
        try:
            # First, make sure the transaction isn't protected by a pack
            status = self._txnMetadata[tid][1]
            if status == PROTECTED_TRANSACTION:
                raise POSException.UndoError, 'Transaction cannot be undone'

            # Calculate all the oids modified in the transaction
            c = self._txnoids.cursor()
            rec = c.set(tid)
            while rec:
                oid = rec[1]
                # In order to be able to undo this transaction, we must be
                # undoing either the current revision of the object, or we
                # must be restoring the exact same pickle (identity compared)
                # that would be restored if we were undoing the current
                # revision.
                revid = self._serials[oid]
                if revid == tid:
                    prevrevid = self._metadata[oid+tid][24:]
                    newrevs.append((oid, self._metadata[oid+prevrevid]))
                else:
                    # Compare the lrevid (pickle pointers) for the current
                    # revision of the object and the revision previous to the
                    # one we're undoing.
                    lrevid = self._metadata[oid+revid][16:24]
                    # When we undo this transaction, the previous record will
                    # become the current record.
                    prevrevid = self._metadata[oid+tid][24:]
                    # And here's the pickle pointer for that potentially
                    # soon-to-be current record
                    prevrec = self._metadata[oid+prevrevid]
                    if lrevid <> prevrec[16:24]:
                        # They aren't the same, so we cannot undo this txn
                        raise POSException.UndoError, 'Cannot undo transaction'
                    newrevs.append((oid, prevrec))
                # Check the next txnoid record
                rec = c.next()
            # Okay, we've checked all the oids affected by the transaction
            # we're about to undo, and everything looks good.  So now we'll
            # write to the log the new object records we intend to commit.
            c.close()
            c = None
            oids = []
            for oid, rec in newrevs:
                vid, nvrevid, lrevid, prevrevid = struct.unpack(
                    '8s8s8s8s', rec)
                self._commitlog.write_moved_object(oid, vid, nvrevid, lrevid,
                                                   prevrevid)
                oids.append(oid)
            return oids
        finally:
            if c:
                c.close()
            self._lock_release()

    def undoLog(self, first, last, filter=None):
        # Get a list of transaction ids that can be undone, based on the
        # determination of the filter.  filter is a function which takes a
        # transaction id and returns true or false.
        #
        # Note that this method has been deprecated by undoInfo() which itself
        # has some flaws, but is the best we have now.  We don't actually need
        # to implement undoInfo() because BaseStorage (which we eventually
        # inherit from) mixes in the UndoLogCompatible class which provides an
        # implementation written in terms of undoLog().
        #
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
            rec = c.get_last()
            while rec and i < last:
                tid, data = rec
                status = data[0]
                if status == PROTECTED_TRANSACTION:
                    break
                userlen, desclen = struct.unpack('>II', data[1:17])
                user = data[17:17+userlen]
                desc = data[17+userlen:17+userlen+desclen]
                ext = data[17+userlen+desclen:]
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
                # And get the previous record
                rec = c.get_prev()
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

    def history(self, oid, version=None, length=1, filter=None):
        # FIXME
        self._lock_acquire()
        try:
            tid=self._current[oid]
        finally: self._lock_release()

    def _zaprevision(self, key, txn):
        # Delete the metadata record pointed to by the key, decrefing the
        # reference counts of the pickle pointed to by this record, and
        # perform cascading decrefs on the referenced objects.
        #
        # We need the lrevid which points to the pickle for this revision...
        vid, nvrevid, lrevid = self._metadata.get(key, txn=txn)[16:24]
        # ...and now delete the metadata record for this object revision
        self._metadata.delete(key, txn=txn)
        # Decref the reference count of the pickle pointed to by oid+lrevid.
        # If the reference count goes to zero, we can garbage collect the
        # pickle, and decref all the objects pointed to by the pickle (with of
        # course, cascading garbage collection).
        pkey = key[:8] + lrevid
        refcount = self._pickleRefcounts.get(pkey, txn=txn)
        # It's possible the pickleRefcounts entry for this oid has already
        # been deleted by a previous pass of _zaprevision().  If so, we're
        # done.
        if refcount is None:
            return
        refcount = utils.U64(refcount) - 1
        if refcount > 0:
            self._pickleRefcounts.put(pkey, utils.p64(refcount), txn=txn)
            return
        # The refcount of this pickle has gone to zero, so we need to garbage
        # collect it, and decref all the objects it points to.
        self._pickleRefcounts.delete(pkey, txn=txn)
        pickle = self._pickles.get(pkey, txn=txn)
        # Sniff the pickle to get the objects it refers to
        collectables = []
        refoids = []
        referencesf(pickle, oids)
        # Now decref the reference counts for each of those objects.  If it
        # goes to zero, remember the oid so we can recursively zap its
        # metadata too.
        for oid in refoids:
            refcount = self._refcounts.get(oid, txn=txn)
            refcount = utils.U64(refcount) - 1
            if refcount > 0:
                self._refcounts.put(oid, utils.p64(refcount), txn=txn)
            else:
                collectables.append(oid)
        # Now for all objects whose refcounts just went to zero, we want to
        # delete any records that pertain to this object.  When we get to
        # deleting the metadata record, we'll do it recursively so as to
        # decref any pickles it points to.  For everything else, we'll do it
        # in the most efficient manner possible.
        tids = []
        for oid in collectables:
            self._serials.delete(oid, txn=txn)
            self._refcounts.delete(oid, txn=txn)
            # To delete all the metadata records associated with this object
            # id, we use a trick of Berkeley cursor objects to only partially
            # specify the key.  This works because keys are compared
            # lexically, with shorter keys collating before longer keys.
            c = self._metadata.cursor()
            try:
                rec = c.set(oid)
                while rec and rec[0][:8] == oid:
                    # Remember the transaction ids so we can clean up the
                    # txnoids table below.  Note that we don't record the vids
                    # because now that we don't have destructive undo,
                    # _zaprevisions() can only be called during a pack() and
                    # it is impossible to pack current records (and hence
                    # currentVersions).
                    tids.append(rec[0][8:])       # second 1/2 of the key
                    self._zaprevision(rec[0], txn)
                    rec = c.next()
            finally:
                c.close()
            # Delete all the txnoids entries that referenced this oid
            for tid in tids:
                c = self._txnoids.cursor(txn=txn)
                try:
                    rec = c.set_both(tid, oid)
                    while rec:
                        # Although unlikely, it is possible that an object got
                        # modified more than once in a transaction.
                        c.delete()
                        rec = c.next_dup()
                finally:
                    c.close()

    def pack(self, t, referencesf):
        # FIXME
        self._lock_acquire()
        try:    
            pass
        finally: self._lock_release()

    # Other interface assertions
    def supportsUndo(self):
        return 1

    def supportsVersions(self):
        return 1
