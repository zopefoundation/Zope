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

# Whitebox testing of storage implementation details.

import unittest

from ZODB.utils import U64
from ZODB.tests.MinPO import MinPO
from ZODB.tests.StorageTestBase import zodb_unpickle
from bsddb3Storage.Minimal import Minimal
from bsddb3Storage.Full import Full
from bsddb3Storage.tests.BerkeleyTestBase import BerkeleyTestBase
from bsddb3Storage.tests.ZODBTestBase import ZODBTestBase

from Persistence import Persistent

ZERO = '\0'*8



class Object(Persistent):
    pass



class WhiteboxLowLevelMinimal(BerkeleyTestBase):
    ConcreteStorage = Minimal

    def checkTableConsistencyAfterCommit(self):
        unless = self.failIf
        eq = self.assertEqual
        oid = self._storage.new_oid()
        revid1 = self._dostore(oid, data=11)
        revid2 = self._dostore(oid, revid=revid1, data=12)
        revid3 = self._dostore(oid, revid=revid2, data=13)
        # First off, there should be no entries in the pending table
        unless(self._storage._pending.keys())
        # Also, there should be no entries in the oids table
        unless(self._storage._oids.keys())
        # Now, there should be exactly one oid in the serials table, and
        # exactly one record for that oid in the table too.
        oids = {}
        c = self._storage._serials.cursor()
        try:
            rec = c.first()
            while rec:
                oid, serial = rec
                oids.setdefault(oid, []).append(serial)
                rec = c.next()
        finally:
            c.close()
        eq(len(oids), 1)
        eq(len(oids[oids.keys()[0]]), 1)
        # There should now be exactly one entry in the pickles table.
        pickles = self._storage._pickles.items()
        eq(len(pickles), 1)
        key, data = pickles[0]
        poid = key[:8]
        pserial = key[8:]
        eq(oid, poid)
        eq(revid3, pserial)
        obj = zodb_unpickle(data)
        eq(obj.value, 13)
        # Now verify the refcounts table, which should be empty because the
        # stored object isn't referenced by any other objects.
        eq(len(self._storage._refcounts.keys()), 0)



class WhiteboxHighLevelMinimal(ZODBTestBase):
    ConcreteStorage = Minimal

    def checkReferenceCounting(self):
        eq = self.assertEqual
        obj = MinPO(11)
        self._root.obj = obj
        get_transaction().commit()
        obj.value = 12
        get_transaction().commit()
        obj.value = 13
        get_transaction().commit()
        # Make sure the databases have what we expect
        eq(len(self._storage._serials.items()), 2)
        eq(len(self._storage._pickles.items()), 2)
        # And now refcount out the object
        del self._root.obj
        get_transaction().commit()
        # Verification stage.  Our serials table should have exactly one
        # entry, oid == 0
        keys = self._storage._serials.keys()
        eq(len(keys), 1)
        eq(len(self._storage._serials.items()), 1)
        eq(keys[0], ZERO)
        # The pickles table now should have exactly one revision of the root
        # object, and no revisions of the MinPO object, which should have been
        # collected away.
        pickles = self._storage._pickles.items()
        eq(len(pickles), 1)
        rec = pickles[0]
        key = rec[0]
        data = rec[1]
        eq(key[:8], ZERO)
        # And that pickle should have no 'obj' attribute.
        unobj = zodb_unpickle(data)
        self.failIf(hasattr(unobj, 'obj'))
        # Our refcounts table should have no entries in it, because the root
        # object is an island.
        eq(len(self._storage._refcounts.keys()), 0)
        # And of course, oids and pendings should be empty too
        eq(len(self._storage._oids.keys()), 0)
        eq(len(self._storage._pending.keys()), 0)

    def checkRecursiveReferenceCounting(self):
        eq = self.assertEqual
        obj1 = Object()
        obj2 = Object()
        obj3 = Object()
        obj4 = Object()
        self._root.obj = obj1
        obj1.obj = obj2
        obj2.obj = obj3
        obj3.obj = obj4
        get_transaction().commit()
        # Make sure the databases have what we expect
        eq(len(self._storage._serials.items()), 5)
        eq(len(self._storage._pickles.items()), 5)
        # And now refcount out the object
        del self._root.obj
        get_transaction().commit()
        # Verification stage.  Our serials table should have exactly one
        # entry, oid == 0
        keys = self._storage._serials.keys()
        eq(len(keys), 1)
        eq(len(self._storage._serials.items()), 1)
        eq(keys[0], ZERO)
        # The pickles table now should have exactly one revision of the root
        # object, and no revisions of any other objects, which should have
        # been collected away.
        pickles = self._storage._pickles.items()
        eq(len(pickles), 1)
        rec = pickles[0]
        key = rec[0]
        data = rec[1]
        eq(key[:8], ZERO)
        # And that pickle should have no 'obj' attribute.
        unobj = zodb_unpickle(data)
        self.failIf(hasattr(unobj, 'obj'))
        # Our refcounts table should have no entries in it, because the root
        # object is an island.
        eq(len(self._storage._refcounts.keys()), 0)
        # And of course, oids and pendings should be empty too
        eq(len(self._storage._oids.keys()), 0)
        eq(len(self._storage._pending.keys()), 0)



class WhiteboxHighLevelFull(ZODBTestBase):
    ConcreteStorage = Full

    def checkReferenceCounting(self):
        eq = self.assertEqual
        # Make sure the databases have what we expect
        eq(len(self._storage._serials.items()), 1)
        eq(len(self._storage._pickles.items()), 1)
        # Now store an object
        obj = MinPO(11)
        self._root.obj = obj
        get_transaction().commit()
        # Make sure the databases have what we expect
        eq(len(self._storage._serials.items()), 2)
        eq(len(self._storage._pickles.items()), 3)
        obj.value = 12
        get_transaction().commit()
        # Make sure the databases have what we expect
        eq(len(self._storage._serials.items()), 2)
        eq(len(self._storage._pickles.items()), 4)
        obj.value = 13
        get_transaction().commit()
        # Make sure the databases have what we expect
        eq(len(self._storage._serials.items()), 2)
        eq(len(self._storage._pickles.items()), 5)
        # And now refcount out the object
        del self._root.obj
        get_transaction().commit()
        # Verification stage.  Our serials tabl should still have 2 entries,
        # one for the root object and one for the now unlinked MinPO obj.
        keys = self._storage._serials.keys()
        eq(len(keys), 2)
        eq(len(self._storage._serials.items()), 2)
        eq(keys[0], ZERO)
        # The pickles table should now have 6 entries, broken down like so:
        # - 3 revisions of the root object: the initial database-open
        #   revision, the revision that got its obj attribute set, and the
        #   revision that got its obj attribute deleted.
        # - 3 Three revisions of obj, corresponding to values 11, 12, and 13
        pickles = self._storage._pickles.items()
        eq(len(pickles), 6)
        # Our refcounts table should have one entry in it for the MinPO that's
        # referenced in an earlier revision of the root object
        eq(len(self._storage._refcounts.keys()), 1)
        # And of course, oids and pendings should be empty too
        eq(len(self._storage._oids.keys()), 0)
        eq(len(self._storage._pending.keys()), 0)



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(WhiteboxLowLevelMinimal, 'check'))
    suite.addTest(unittest.makeSuite(WhiteboxHighLevelMinimal, 'check'))
    suite.addTest(unittest.makeSuite(WhiteboxHighLevelFull, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
