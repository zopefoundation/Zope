"""Berkeley storage without undo or versioning.

See Full.py for an implementation of Berkeley storage that does support undo
and versioning.
"""

__version__ = '$Revision: 1.11 $'[-2:][0]

# This uses the Dunn/Kuchling PyBSDDB v3 extension module available from
# http://pybsddb.sourceforge.net.  It is compatible with release 3.0 of
# PyBSDDB3.
from bsddb3 import db

# BerkeleyBase.BerkeleyBase class provides some common functionality for both
# the Full and Minimal implementations.  It in turn inherits from
# ZODB.BaseStorage.BaseStorage which itself provides some common storage
# functionality.
from BerkeleyBase import BerkeleyBase
from CommitLog import PacklessLog
from ZODB import POSException
from ZODB import utils


class Minimal(BerkeleyBase):
    #
    # Overrides of base class methods
    #
    def _setupDBs(self):
        # Create the tables used to maintain the relevant information.  The
        # minimal storage needs two tables:
        #
        #   serials -- maps object ids (oids) to object serial numbers.  The
        #              serial number is essentially a timestamp used to
        #              determine if conflicts have arisen.  If an attempt is
        #              made to store an object with a serial number that is
        #              different than the serial number we already have for
        #              the object, a ConflictError is raised.
        #
        #   pickles -- maps oids to the object's data pickles.
        #
        self._serials = self._setupDB('serials')
        self._pickles = self._setupDB('pickles')

    def _begin(self, tid, u, d, e):
        # Begin the current transaction.  Currently this just makes sure that
        # the commit log is in the proper state.
        if self._commitlog is None:
            # JF: Chris was getting some weird errors / bizarre behavior from
            # Berkeley when using an existing directory or having non-BSDDB
            # files in that directory.
            self._commitlog = PacklessLog(dir=self._env.db_home)
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
        #
        # u is the user associated with the transaction, used for
        #   auditing, etc.
        #
        # d is the description of the transaction, arbitrary string,
        #   but might contain path information
        #
        # e is the transaction extension, extra metadata about the
        #   transaction, such quotas or other custom storage
        #   policies.
        txn = self._env.txn_begin()
        try:
            # BAW: all objects have the same serial number?  JF: all the
            # existing storages re-use the transaction's serial number for all
            # the objects, but they don't have to.  In Jeremy's SimpleStorage,
            # it's just a counter.  _serial is set in BaseStorage.py during
            # tpc_begin().
            serial = self._serial
            while 1:
                rec = self._commitlog.next()
                if rec is None:
                    break
                oid, pickle = rec
                # Put the object's serial number
                self._serials.put(oid, serial, txn)
                # Put the object's pickle data
                self._pickles.put(oid, pickle, txn)
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

    def _abort(self):
        # Throw away the current transaction.  Since we don't have a
        # transaction open to Berkeley, what this really means is that we're
        # done with our commit log, so we should reset it.
        self._closelog()

    def close(self):
        # BAW: the original implementation also deleted these attributes.  Was
        # that just to reclaim the garbage?
        self._serials.close()
        self._pickles.close()
        # Base class implements some useful close behavior
        BerkeleyBase.close(self)

    #
    # Public storage interface
    #

    def load(self, oid, version):
        """Return the object pickle and serial number for the object
        referenced by object id `oid'.  The object is loaded from the back-end
        storage.

        `version' is required by the storage interface, but it is ignored
        because undo and versions are not supported.
        """
        self._lock_acquire()
        try:
            serial = self._serials[oid]
            pickle = self._pickles[oid]
            return pickle, serial
        finally:
            self._lock_release()

    def store(self, oid, serial, data, version, transaction):
        """Store the object referenced by `oid'.

        The object is stored to the transaction named by `transaction', in
        preparation for the commit or abort of the transaction (i.e. it is not
        stored to the underlying database yet).

        `serial' is the serial number of the object.  If it does not match the
        stored serial number, a ConflictError is raised.

        `data' is object's data pickle.

        `version' is required by the storage interface, but it must be set to
        None because undo and versions are not supported.
        """
        if transaction is not self._transaction:
            raise POSException.StorageTransactionError(self, transaction)

        # Make sure the version is false.  Usually it's an empty string, but
        # we have to make sure.
        if version:
            raise POSException.Unsupported, "Versions aren't supported"

        self._lock_acquire()
        try:
            oserial = self._serials.get(oid)
            if oserial is not None and serial <> oserial:
                # The object exists in the database, but the serial number
                # given in the call is not the same as the last stored serial
                # number.  Raise a ConflictError.
                raise POSException.ConflictError(
                    'serial number mismatch (was: %s, has: %s)' %
                    (utils.U64(oserial), utils.U64(serial)))
            # Our serial number is updated in BaseStorage's tpc_begin() call,
            # which sets the serial number to the current timestamp.
            serial = self._serial
            # Write the object's pickle data to the commit log file
            self._commitlog.write_object(oid, data)
        finally:
            self._lock_release()
        # Return our cached serial number for the object
        return serial

    def pack(self, t, getrefsfunc):
        """Pack the storage.

        Since this storage does not support versions, packing serves only to
        remove any objects that are not referenced from the root of the tree
        (i.e. they are garbage collected).

        BAW: where are `t' and `getrefsfunc' defined in the model?  And
        exactly what are their purpose and semantics?
        """
        self._lock_acquire()
        try:
            # Build an index only of those objects reachable from the root.
            # Unfortunately, we do this in memory, so the memory footprint of
            # packing may still be substantial.
            #
            # Known root objects are kept in this list and as new ones are
            # found, their oids are pushed onto the front of the list. It is
            # also added to the seen dictionary, which keeps track of objects
            # we've seen already.  When roots is empty, we're done visiting
            # all the objects.
            roots = ['\0\0\0\0\0\0\0\0']
            seen = {}
            while roots:
                # Get the next oid from the roots list
                oid = roots.pop()
                # Skip it if we've already seen it
                if seen.has_key(oid):
                    continue
                # Get the pickle corresponding to the object id and scan it
                # for references to other objects.  This is done by the
                # magical `getrefsfunc' function given as an argument.
                pickle = self._pickles[oid]
                seen[oid] = 1
                # This will prepend any new oids we'll need to scan
                getrefsfunc(pickle, roots)
            # Now, go through every oid for which we have a pickle, and if we
            # have not seen it, then it must be garbage (because it was never
            # reached from one of the roots).  In that case, delete its entry
            # in the pickle index.
            for oid in self._pickles.keys():
                if not seen.has_key(oid):
                    del self._pickles[oid]
        finally:
            self._lock_release()
