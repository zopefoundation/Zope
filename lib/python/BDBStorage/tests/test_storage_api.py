# Run tests against the official storage API as described in
# http://www.zope.org/Documentation/Developer/Models/ZODB/ZODB_Architecture_Storage_Interface_Info.html

import os
import errno
import pickle
import unittest
import test_create

from ZODB import utils
from ZODB.Transaction import Transaction
from ZODB import POSException

DBHOME = 'test-db'
ZERO = '\0'*8



class StorageAPI(test_create.BaseFramework):
    def setUp(self):
        # A simpler setUp() than the base class since we don't need the DB
        # object, the connection, or the root.
        self._dbhome = DBHOME
        os.mkdir(self._dbhome)

        try:
            self._storage = self.ConcreteStorage(self._dbhome)
        except:
            self.tearDown()
            raise
        self._transaction = Transaction()

    def _close(self):
        self._transaction.abort()
        self._storage.close()

    def checkBasics(self):
        self._storage.tpc_begin(self._transaction)
        # This should simply return
        self._storage.tpc_begin(self._transaction)
        # Aborting is easy
        self._storage.tpc_abort(self._transaction)
        # Test a few expected exceptions when we're doing operations giving a
        # different Transaction object than the one we've begun on.
        self._storage.tpc_begin(self._transaction)
        self.assertRaises(
            POSException.StorageTransactionError,
            self._storage.store,
            0, 0, 0, 0, Transaction())
        self.assertRaises(
            POSException.StorageTransactionError,
            self._storage.abortVersion,
            0, Transaction())
        self.assertRaises(
            POSException.StorageTransactionError,
            self._storage.commitVersion,
            0, 1, Transaction())
        self.assertRaises(
            POSException.StorageTransactionError,
            self._storage.store,
            0, 1, 2, 3, Transaction())
        self._storage.tpc_abort(self._transaction)

    def _dostore(self, oid=None, revid=None, data=None, version=None):
        # Defaults
        if oid is None:
            oid = self._storage.new_oid()
        if revid is None:
            revid = ZERO
        if data is None:
            data = pickle.dumps(7)
        else:
            data = pickle.dumps(data)
        if version is None:
            version = ''
        # Begin the transaction
        self._storage.tpc_begin(self._transaction)
        # Store an object
        newrevid = self._storage.store(oid, revid, data, version,
                                       self._transaction)
        # Finish the transaction
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        return newrevid
        
    def checkNonVersionStore(self, oid=None, revid=None, version=None):
        revid = ZERO
        newrevid = self._dostore(revid=revid)
        # Finish the transaction.
        assert newrevid <> revid

    def checkLen(self):
        # The length of the database ought to grow by one each time
        assert len(self._storage) == 0
        self._dostore()
        assert len(self._storage) == 1
        self._dostore()
        assert len(self._storage) == 2

    def checkNonVersionStoreAndLoad(self):
        oid = self._storage.new_oid()
        self._dostore(oid=oid, data=7)
        data, revid = self._storage.load(oid, '')
        value = pickle.loads(data)
        assert value == 7
        # Now do a bunch of updates to an object
        for i in range(13, 22):
            revid = self._dostore(oid, revid=revid, data=i)
        # Now get the latest revision of the object
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 21

    def checkNonVersionModifiedInVersion(self):
        oid = self._storage.new_oid()
        self._dostore(oid=oid)
        assert self._storage.modifiedInVersion(oid) == ''

    def checkLoadSerial(self):
        oid = self._storage.new_oid()
        revid = ZERO
        revisions = {}
        for i in range(31, 38):
            revid = self._dostore(oid, revid=revid, data=i)
            revisions[revid] = i
        # Now make sure all the revisions have the correct value
        for revid, value in revisions.items():
            data = self._storage.loadSerial(oid, revid)
            assert pickle.loads(data) == value

    def checkVersionedStoreAndLoad(self):
        # Store a couple of non-version revisions of the object
        oid = self._storage.new_oid()
        revid = self._dostore(oid, data=11)
        revid = self._dostore(oid, revid=revid, data=12)
        # And now store some new revisions in a version
        version = 'test-version'
        revid = self._dostore(oid, revid=revid, data=13, version=version)
        revid = self._dostore(oid, revid=revid, data=14, version=version)
        revid = self._dostore(oid, revid=revid, data=15, version=version)
        # Now read back the object in both the non-version and version and
        # make sure the values jive.
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 12
        data, revid = self._storage.load(oid, version)
        assert pickle.loads(data) == 15

    def checkVersionedLoadErrors(self):
        oid = self._storage.new_oid()
        version = 'test-version'
        revid = self._dostore(oid, data=11)
        revid = self._dostore(oid, revid=revid, data=12, version=version)
        # Try to load a bogus oid
        self.assertRaises(KeyError,
                          self._storage.load,
                          self._storage.new_oid(), '')
        # Try to load a bogus version string
        self.assertRaises(POSException.VersionError,
                          self._storage.load,
                          oid, 'bogus')

    def checkConflicts(self):
        oid = self._storage.new_oid()
        revid1 = self._dostore(oid, data=11)
        revid2 = self._dostore(oid, revid=revid1, data=12)
        self.assertRaises(POSException.ConflictError,
                          self._dostore,
                          oid, revid=revid1, data=13)

    def checkVersionLock(self):
        oid = self._storage.new_oid()
        revid = self._dostore(oid, data=11)
        version = 'test-version'
        revid = self._dostore(oid, revid=revid, data=12, version=version)
        self.assertRaises(POSException.VersionLockError,
                          self._dostore,
                          oid, revid=revid, data=14,
                          version='another-version')

    def checkVersionEmpty(self):
        # Before we store anything, these versions ought to be empty
        version = 'test-version'
        assert self._storage.versionEmpty('')
        assert self._storage.versionEmpty(version)
        # Now store some objects
        oid = self._storage.new_oid()
        revid = self._dostore(oid, data=11)
        revid = self._dostore(oid, revid=revid, data=12)
        revid = self._dostore(oid, revid=revid, data=13, version=version)
        revid = self._dostore(oid, revid=revid, data=14, version=version)
        # The blank version should not be empty
        assert not self._storage.versionEmpty('')
        # Neither should 'test-version'
        assert not self._storage.versionEmpty(version)
        # But this non-existant version should be empty
        assert self._storage.versionEmpty('bogus')

    def checkVersions(self):
        # Store some objects in the non-version
        oid1 = self._storage.new_oid()
        oid2 = self._storage.new_oid()
        oid3 = self._storage.new_oid()
        revid1 = self._dostore(oid1, data=11)
        revid2 = self._dostore(oid2, data=12)
        revid3 = self._dostore(oid3, data=13)
        # Now create some new versions
        revid1 = self._dostore(oid1, revid=revid1, data=14, version='one')
        revid2 = self._dostore(oid2, revid=revid2, data=15, version='two')
        revid3 = self._dostore(oid3, revid=revid3, data=16, version='three')
        # Ask for the versions
        versions = self._storage.versions()
        assert 'one' in versions
        assert 'two' in versions
        assert 'three' in versions
        # Now flex the `max' argument
        versions = self._storage.versions(1)
        assert len(versions) == 1
        assert 'one' in versions or 'two' in versions or 'three' in versions

    def _setup_version(self, version='test-version'):
        # Store some revisions in the non-version
        oid = self._storage.new_oid()
        revid = self._dostore(oid, data=49)
        revid = self._dostore(oid, revid=revid, data=50)
        nvrevid = revid = self._dostore(oid, revid=revid, data=51)
        # Now do some stores in a version
        revid = self._dostore(oid, revid=revid, data=52, version=version)
        revid = self._dostore(oid, revid=revid, data=53, version=version)
        revid = self._dostore(oid, revid=revid, data=54, version=version)
        return oid, version

    def checkAbortVersion(self):
        oid, version = self._setup_version()
        # Now abort the version -- must be done in a transaction
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.abortVersion(version, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 51

    def checkAbortVersionErrors(self):
        oid, version = self._setup_version()
        # Now abort a bogus version
        self._storage.tpc_begin(self._transaction)
        self.assertRaises(KeyError,
                          self._storage.abortVersion,
                          'bogus', self._transaction)
        # And try to abort the empty version
        self.assertRaises(KeyError,
                          self._storage.abortVersion,
                          '', self._transaction)
        # But now we really try to abort the version
        oids = self._storage.abortVersion(version, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 51

    def checkModifyAfterAbortVersion(self):
        oid, version = self._setup_version()
        # Now abort the version
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.abortVersion(version, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        # Load the object's current state (which gets us the revid)
        data, revid = self._storage.load(oid, '')
        # And modify it a few times
        revid = self._dostore(oid, revid=revid, data=52)
        revid = self._dostore(oid, revid=revid, data=53)
        revid = self._dostore(oid, revid=revid, data=54)
        data, newrevid = self._storage.load(oid, '')
        assert newrevid == revid
        assert pickle.loads(data) == 54

    def checkCommitToNonVersion(self):
        oid, version = self._setup_version()
        data, revid = self._storage.load(oid, version)
        assert pickle.loads(data) == 54
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 51
        # Try committing this version to the empty version
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.commitVersion(version, '', self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 54

    def checkCommitToOtherVersion(self):
        oid1, version1 = self._setup_version('one')
        data, revid1 = self._storage.load(oid1, version1)
        assert pickle.loads(data) == 54
        oid2, version2 = self._setup_version('two')
        data, revid2 = self._storage.load(oid2, version2)
        assert pickle.loads(data) == 54
        # Let's make sure we can't get object1 in version2
        self.assertRaises(POSException.VersionError,
                          self._storage.load, oid1, version2)
        # Okay, now let's commit object1 to version2
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.commitVersion(version1, version2,
                                           self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid1
        data, revid = self._storage.load(oid1, version2)
        assert pickle.loads(data) == 54
        data, revid = self._storage.load(oid2, version2)
        assert pickle.loads(data) == 54
        self.assertRaises(POSException.VersionError,
                          self._storage.load, oid1, version1)

    def checkAbortOneVersionCommitTheOther(self):
        oid1, version1 = self._setup_version('one')
        data, revid1 = self._storage.load(oid1, version1)
        assert pickle.loads(data) == 54
        oid2, version2 = self._setup_version('two')
        data, revid2 = self._storage.load(oid2, version2)
        assert pickle.loads(data) == 54
        # Let's make sure we can't get object1 in version2
        self.assertRaises(POSException.VersionError,
                          self._storage.load, oid1, version2)
        # First, let's abort version1
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.abortVersion(version1, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid1
        data, revid = self._storage.load(oid1, '')
        assert pickle.loads(data) == 51
        self.assertRaises(POSException.VersionError,
                          self._storage.load, oid1, version1)
        self.assertRaises(POSException.VersionError,
                          self._storage.load, oid1, version2)
        data, revid = self._storage.load(oid2, '')
        assert pickle.loads(data) == 51
        data, revid = self._storage.load(oid2, version2)
        assert pickle.loads(data) == 54
        # Okay, now let's commit version2 back to the trunk
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.commitVersion(version2, '', self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid2
        # These objects should not be found in version 2
        self.assertRaises(POSException.VersionError,
                          self._storage.load, oid1, version2)
        self.assertRaises(POSException.VersionError,
                          self._storage.load, oid2, version2)
        # But the trunk should be up to date now
        data, revid = self._storage.load(oid2, '')
        assert pickle.loads(data) == 54

    def checkSimpleTransactionalUndo(self):
        oid = self._storage.new_oid()
        revid = self._dostore(oid, data=23)
        revid = self._dostore(oid, revid=revid, data=24)
        revid = self._dostore(oid, revid=revid, data=25)
        # Now start an undo transaction
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 24
        # Do another one
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 23
        # Try to undo the first record
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        # This should fail since we've undone the object's creation
        self.assertRaises(KeyError,
                          self._storage.load, oid, '')
        # But it's really a more specific type of error
        import Full
        self.assertRaises(Full.ObjectDoesNotExist,
                          self._storage.load, oid, '')
        # And now let's try to redo the object's creation
        try:
            self._storage.load(oid, '')
        except Full.ObjectDoesNotExist, e:
            revid = e.revid
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 23

    def checkTwoObjectUndo(self):
        # Convenience
        p31, p32, p51, p52 = map(pickle.dumps, (31, 32, 51, 52))
        oid1 = self._storage.new_oid()
        oid2 = self._storage.new_oid()
        revid1 = revid2 = ZERO
        # Store two objects in the same transaction
        self._storage.tpc_begin(self._transaction)
        revid1 = self._storage.store(oid1, revid1, p31, '', self._transaction)
        revid2 = self._storage.store(oid2, revid2, p51, '', self._transaction)
        # Finish the transaction
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert revid1 == revid2
        # Update those same two objects
        self._storage.tpc_begin(self._transaction)
        revid1 = self._storage.store(oid1, revid1, p32, '', self._transaction)
        revid2 = self._storage.store(oid2, revid2, p52, '', self._transaction)
        # Finish the transaction
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert revid1 == revid2
        # Make sure the objects have the current value
        data, revid1 = self._storage.load(oid1, '')
        assert pickle.loads(data) == 32
        data, revid2 = self._storage.load(oid2, '')
        assert pickle.loads(data) == 52
        # Now attempt to undo the transaction containing two objects
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid1, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 2
        assert oid1 in oids and oid2 in oids
        data, revid1 = self._storage.load(oid1, '')
        assert pickle.loads(data) == 31
        data, revid2 = self._storage.load(oid2, '')
        assert pickle.loads(data) == 51

    def checkTwoObjectUndoAgain(self):
        p32, p33, p52, p53 = map(pickle.dumps, (32, 33, 52, 53))
        # Like the above, but the first revision of the objects are stored in
        # different transactions.
        oid1 = self._storage.new_oid()
        oid2 = self._storage.new_oid()
        revid1 = self._dostore(oid1, data=31)
        revid2 = self._dostore(oid2, data=51)
        # Update those same two objects
        self._storage.tpc_begin(self._transaction)
        revid1 = self._storage.store(oid1, revid1, p32, '', self._transaction)
        revid2 = self._storage.store(oid2, revid2, p52, '', self._transaction)
        # Finish the transaction
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert revid1 == revid2
        # Now attempt to undo the transaction containing two objects
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid1, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 2
        assert oid1 in oids and oid2 in oids
        data, revid1 = self._storage.load(oid1, '')
        assert pickle.loads(data) == 31
        data, revid2 = self._storage.load(oid2, '')
        assert pickle.loads(data) == 51
        # Like the above, but this time, the second transaction contains only
        # one object.
        self._storage.tpc_begin(self._transaction)
        revid1 = self._storage.store(oid1, revid1, p33, '', self._transaction)
        revid2 = self._storage.store(oid2, revid2, p53, '', self._transaction)
        # Finish the transaction
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert revid1 == revid2
        # Update in different transactions
        revid1 = self._dostore(oid1, revid=revid1, data=34)
        revid2 = self._dostore(oid2, revid=revid2, data=54)
        # Now attempt to undo the transaction containing two objects
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid1, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oid1 in oids and not oid2 in oids
        data, revid1 = self._storage.load(oid1, '')
        assert pickle.loads(data) == 33
        data, revid2 = self._storage.load(oid2, '')
        assert pickle.loads(data) == 54

    def checkNotUndoable(self):
        # Set things up so we've got a transaction that can't be undone
        oid = self._storage.new_oid()
        revid_a = self._dostore(oid, data=51)
        revid_b = self._dostore(oid, revid=revid_a, data=52)
        revid_c = self._dostore(oid, revid=revid_b, data=53)
        # Start the undo
        self._storage.tpc_begin(self._transaction)
        self.assertRaises(POSException.UndoError,
                          self._storage.transactionalUndo,
                          revid_b, self._transaction)
        self._storage.tpc_abort(self._transaction)
        # Now have more fun: object1 and object2 are in the same transaction,
        # which we'll try to undo to, but one of them has since modified in
        # different transaction, so the undo should fail.
        oid1 = oid
        revid1 = revid_c
        oid2 = self._storage.new_oid()
        revid2 = ZERO
        p81, p82, p91, p92 = map(pickle.dumps, (81, 82, 91, 92))
        self._storage.tpc_begin(self._transaction)
        revid1 = self._storage.store(oid1, revid1, p81, '', self._transaction)
        revid2 = self._storage.store(oid2, revid2, p91, '', self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert revid1 == revid2
        # Make sure the objects have the expected values
        data, revid_11 = self._storage.load(oid1, '')
        assert pickle.loads(data) == 81
        data, revid_22 = self._storage.load(oid2, '')
        assert pickle.loads(data) == 91
        assert revid_11 == revid1 and revid_22 == revid2
        # Now modify oid2
        revid2 = self._dostore(oid2, revid=revid2, data=p92)
        assert revid1 <> revid2 and revid2 <> revid_22
        self._storage.tpc_begin(self._transaction)
        self.assertRaises(POSException.UndoError,
                          self._storage.transactionalUndo,
                          revid1, self._transaction)
        self.assertRaises(POSException.UndoError,
                          self._storage.transactionalUndo,
                          revid_22, self._transaction)
        self._storage.tpc_abort(self._transaction)

    def checkUndoInVersion(self):
        oid = self._storage.new_oid()
        version = 'one'
        revid_a = self._dostore(oid, data=91)
        revid_b = self._dostore(oid, revid=revid_a, data=92, version=version)
        revid_c = self._dostore(oid, revid=revid_b, data=93, version=version)
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid_c, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        data, revid = self._storage.load(oid, '')
        assert revid == revid_a
        assert pickle.loads(data) == 91
        data, revid = self._storage.load(oid, version)
        assert revid > revid_b and revid > revid_c
        assert pickle.loads(data) == 92
        # Now commit the version...
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.commitVersion(version, '', self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        self.assertRaises(POSException.VersionError,
                          self._storage.load,
                          oid, version)
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 92
        # ...and undo the commit
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        data, revid = self._storage.load(oid, version)
        assert pickle.loads(data) == 92
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 91
        # Now abort the version
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.abortVersion(version, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        # The object should not exist in the version now, but it should exist
        # in the non-version
        self.assertRaises(POSException.VersionError,
                          self._storage.load,
                          oid, version)
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 91
        # Now undo the abort
        self._storage.tpc_begin(self._transaction)
        oids = self._storage.transactionalUndo(revid, self._transaction)
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)
        assert len(oids) == 1
        assert oids[0] == oid
        # And the object should be back in versions 'one' and ''
        data, revid = self._storage.load(oid, version)
        assert pickle.loads(data) == 92
        data, revid = self._storage.load(oid, '')
        assert pickle.loads(data) == 91



class FullStorageAPI(StorageAPI):
    import Full
    ConcreteStorage = Full.Full


class MinimalStorageAPI(StorageAPI):
    import Minimal
    ConcreteStorage = Minimal.Minimal

    def checkLoadSerial(self):
        # This storage doesn't support versions, so we should get an exception
        self.assertRaises(POSException.Unsupported,
                          StorageAPI.checkLoadSerial,
                          self)

    def checkVersionedStoreAndLoad(self):
        # This storage doesn't support versions, so we should get an exception
        self.assertRaises(POSException.Unsupported,
                          StorageAPI.checkVersionedStoreAndLoad,
                          self)



def suite():
    suite = unittest.TestSuite()
    # Minimal storage tests
    suite.addTest(MinimalStorageAPI('checkBasics'))
    suite.addTest(MinimalStorageAPI('checkNonVersionStore'))
    suite.addTest(MinimalStorageAPI('checkLen'))
    suite.addTest(MinimalStorageAPI('checkNonVersionStoreAndLoad'))
    suite.addTest(MinimalStorageAPI('checkNonVersionModifiedInVersion'))
    suite.addTest(MinimalStorageAPI('checkLoadSerial'))
    suite.addTest(MinimalStorageAPI('checkVersionedStoreAndLoad'))
    # Skipping: MinimalStorageAPI.checkVersionedLoadErrors()
    suite.addTest(MinimalStorageAPI('checkConflicts'))
    # Skipping: MinimalStorageAPI.checkVersionLock()
    # Skipping: MinimalStorageAPI.checkVersionEmpty()
    # Skipping: MinimalStorageAPI.checkVersions()
    # Skipping: MinimalStorageAPI.checkAbortVersion()
    # Skipping: MinimalStorageAPI.checkAbortVersionErrors()
    # Skipping: MinimalStorageAPI.checkModifyAfterAbortVersion()
    # Skipping: MinimalStorageAPI.checkCommitToNonVersion()
    # Skipping: MinimalStorageAPI.checkCommitToOtherVersion()
    # Skipping: MinimalStorageAPI.checkAbortOneVersionCommitTheOther()
    # Skipping: MinimalStorageAPI.checkSimpleTransactionalUndo()
    # Skipping: MinimalStorageAPI.checkTwoObjectUndo()
    # Skipping: MinimalStorageAPI.checkTwoObjectUndoAgain()
    # Skipping: MinimalStorageAPI.checkNotUndoable()
    # Skipping: MinimalStorageAPI.checkUndoInVersion()
    # Full storage tests
    suite.addTest(FullStorageAPI('checkBasics'))
    suite.addTest(FullStorageAPI('checkNonVersionStore'))
    suite.addTest(FullStorageAPI('checkLen'))
    suite.addTest(FullStorageAPI('checkNonVersionStoreAndLoad'))
    suite.addTest(FullStorageAPI('checkNonVersionModifiedInVersion'))
    suite.addTest(FullStorageAPI('checkLoadSerial'))
    suite.addTest(FullStorageAPI('checkVersionedStoreAndLoad'))
    suite.addTest(FullStorageAPI('checkVersionedLoadErrors'))
    suite.addTest(FullStorageAPI('checkConflicts'))
    suite.addTest(FullStorageAPI('checkVersionLock'))
    suite.addTest(FullStorageAPI('checkVersionEmpty'))
    suite.addTest(FullStorageAPI('checkVersions'))
    suite.addTest(FullStorageAPI('checkAbortVersion'))
    suite.addTest(FullStorageAPI('checkAbortVersionErrors'))
    suite.addTest(FullStorageAPI('checkModifyAfterAbortVersion'))
    suite.addTest(FullStorageAPI('checkCommitToNonVersion'))
    suite.addTest(FullStorageAPI('checkCommitToOtherVersion'))
    suite.addTest(FullStorageAPI('checkAbortOneVersionCommitTheOther'))
    suite.addTest(FullStorageAPI('checkSimpleTransactionalUndo'))
    suite.addTest(FullStorageAPI('checkTwoObjectUndo'))
    suite.addTest(FullStorageAPI('checkTwoObjectUndoAgain'))
    suite.addTest(FullStorageAPI('checkNotUndoable'))
    suite.addTest(FullStorageAPI('checkUndoInVersion'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
