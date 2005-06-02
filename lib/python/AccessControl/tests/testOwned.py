"""Unit tests for AccessControl.Owned

$Id$
"""

import unittest
import Testing
import ZODB

from Acquisition import Implicit, aq_inner

class FauxUser(Implicit):

    def __init__(self, id):
        self._id = id

    def getId(self):
        return self._id

class FauxUserFolder(Implicit):

    def getUserById(self, id, default):
        return FauxUser(id)

class FauxRoot(Implicit):

    def getPhysicalRoot(self):
        return aq_inner(self)

    def unrestrictedTraverse(self, path, default=None):

        if type(path) is type(''):
            path = path.split('/')

        if not path[0]:
            path = path[1:]

        obj = self

        try:
            while path:
                next, path = path[0], path[1:]
                obj = getattr(obj, next)
        except AttributeError:
            obj = default

        return obj

class OwnedTests(unittest.TestCase):

    def _getTargetClass(self):
        from AccessControl.Owned import Owned
        return Owned

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeDummy(self, *args, **kw):

        from AccessControl.Owned import Owned
        class Dummy(Implicit, Owned):
            pass

        return Dummy(*args, **kw)

    def test_z3interfaces(self):
        from AccessControl.interfaces import IOwned
        from AccessControl.Owned import Owned
        from zope.interface.verify import verifyClass

        verifyClass(IOwned, Owned)

    def test_getOwnerTuple_unowned(self):
        owned = self._makeOne()

        owner_tuple = owned.getOwnerTuple()

        self.assertEqual(owner_tuple, None)

    def test_getOwnerTuple_simple(self):
        owned = self._makeOne()
        owned._owner = ('/foobar', 'baz')

        owner_tuple = owned.getOwnerTuple()

        self.assertEqual(len(owner_tuple), 2)
        self.assertEqual(owner_tuple[0], '/foobar')
        self.assertEqual(owner_tuple[1], 'baz')

    def test_getOwnerTuple_acquired(self):

        root = FauxRoot()
        root._owner = ('/foobar', 'baz')
        owned = self._makeDummy().__of__(root)
        owner_tuple = owned.getOwnerTuple()

        self.assertEqual(len(owner_tuple), 2)
        self.assertEqual(owner_tuple[0], '/foobar')
        self.assertEqual(owner_tuple[1], 'baz')

    def test_getOwnerTuple_acquired_no_tricks(self):

        # Ensure that we acquire ownership only through containment.
        root = FauxRoot()
        root._owner = ('/foobar', 'baz')
        owned = self._makeDummy().__of__(root)
        owner_tuple = owned.getOwnerTuple()

        tricky = self._makeDummy()
        tricky._owner = ('/bambam', 'qux')
        tricky = tricky.__of__(root)

        not_tricked = owned.__of__(tricky)
        owner_tuple = not_tricked.getOwnerTuple()

        self.assertEqual(len(owner_tuple), 2)
        self.assertEqual(owner_tuple[0], '/foobar')
        self.assertEqual(owner_tuple[1], 'baz')

    def test_getWrappedOwner_unowned(self):

        owned = self._makeOne()

        wrapped_owner = owned.getWrappedOwner()

        self.assertEqual(wrapped_owner, None)

    def test_getWrappedOwner_unownable(self):
        from AccessControl.Owned import UnownableOwner
        owned = self._makeOne()
        owned._owner = UnownableOwner

        wrapped_owner = owned.getWrappedOwner()

        self.assertEqual(wrapped_owner, None)

    def test_getWrappedOwner_simple(self):

        root = FauxRoot()
        root.acl_users = FauxUserFolder()

        owned = self._makeDummy().__of__(root)
        owned._owner = ('/acl_users', 'user')

        wrapped_owner = owned.getWrappedOwner()

        self.assertEqual(wrapped_owner.getId(), 'user')

    def test_getWrappedOwner_acquired(self):

        root = FauxRoot()
        root._owner = ('/acl_users', 'user')
        root.acl_users = FauxUserFolder()

        owned = self._makeDummy().__of__(root)

        wrapped_owner = owned.getWrappedOwner()

        self.assertEqual(wrapped_owner.getId(), 'user')

    def test_getWrappedOwner_acquired_no_tricks(self):

        root = FauxRoot()
        root._owner = ('/acl_users', 'user')
        root.acl_users = FauxUserFolder()

        owned = self._makeDummy().__of__(root)

        tricky = self._makeDummy()
        tricky._owner = ('/acl_users', 'black_hat')
        tricky = tricky.__of__(root)

        not_tricked = owned.__of__(tricky)

        wrapped_owner = not_tricked.getWrappedOwner()

        self.assertEqual(wrapped_owner.getId(), 'user')


def test_suite():
    return unittest.makeSuite(OwnedTests)

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
