from unittest import TestCase, TestSuite, makeSuite, main

import Zope
Zope.startup()
from Interface.Verify import verifyClass

from OFS.CopySupport import CopySource
from OFS.ObjectManager import ObjectManager
from OFS.OrderSupport import OrderSupport

class DummyObject(CopySource):
    def __init__(self, id, meta_type):
        self.id = id
        self.meta_type = meta_type
    def cb_isMoveable(self):
        return 1
    def manage_afterAdd(self, item, container):
        return
    def wl_isLocked(self):
        return 0

class OrderedObjectManager(OrderSupport, ObjectManager):
    # disable permission verification
    def _verifyObjectPaste(self, object, validate_src=1):
        return


class TestOrderSupport(TestCase):

    def _makeOne(self):
        f = OrderedObjectManager()
        f._objects = ( {'id':'o1', 'meta_type':'mt1'}
                     , {'id':'o2', 'meta_type':'mt2'}
                     , {'id':'o3', 'meta_type':'mt1'}
                     , {'id':'o4', 'meta_type':'mt2'}
                     )
        f.o1 = DummyObject('o1', 'mt1')
        f.o2 = DummyObject('o2', 'mt2')
        f.o3 = DummyObject('o3', 'mt1')
        f.o4 = DummyObject('o4', 'mt2')
        return f

    def _doCanonTestA(self, methodname, table):
        for arg1, order, rval in table:
            f = self._makeOne()
            method = getattr(f, methodname)
            if rval == 'ValueError':
                self.failUnlessRaises( ValueError, method, arg1 )
            else:
                self.failUnlessEqual( method(arg1), rval )
            self.failUnlessEqual( f.objectIds(), order )

    def _doCanonTestB(self, methodname, table):
        for arg1, arg2, order, rval in table:
            f = self._makeOne()
            method = getattr(f, methodname)
            if rval == 'ValueError':
                self.failUnlessRaises( ValueError, method, arg1, arg2 )
            else:
                self.failUnlessEqual( method(arg1, arg2), rval )
            self.failUnlessEqual( f.objectIds(), order )

    def test_moveObjectsUp(self):
        self._doCanonTestB( 'moveObjectsUp',
              ( ( 'o4', 1,         ['o1', 'o2', 'o4', 'o3'], 1 )
              , ( 'o4', 2,         ['o1', 'o4', 'o2', 'o3'], 1 )
              , ( ('o1', 'o3'), 1, ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ('o1', 'o3'), 9, ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ('o2', 'o3'), 1, ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ('n2', 'o3'), 1, ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ('o3', 'o1'), 1, ['o1', 'o3', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsDown(self):
        self._doCanonTestB( 'moveObjectsDown',
              ( ( 'o1', 1,         ['o2', 'o1', 'o3', 'o4'], 1 )
              , ( 'o1', 2,         ['o2', 'o3', 'o1', 'o4'], 1 )
              , ( ('o2', 'o4'), 1, ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ('o2', 'o4'), 9, ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ('o2', 'o3'), 1, ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ('n2', 'o3'), 1, ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ('o4', 'o2'), 1, ['o1', 'o3', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsToTop(self):
        self._doCanonTestA( 'moveObjectsToTop',
              ( ( 'o4',         ['o4', 'o1', 'o2', 'o3'], 1 )
              , ( ('o1', 'o3'), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ('o2', 'o3'), ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ('n2', 'o3'), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ('o3', 'o1'), ['o3', 'o1', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsToBottom(self):
        self._doCanonTestA( 'moveObjectsToBottom',
              ( ( 'o1',         ['o2', 'o3', 'o4', 'o1'], 1 )
              , ( ('o2', 'o4'), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ('o2', 'o3'), ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ('n2', 'o3'), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ('o4', 'o2'), ['o1', 'o3', 'o4', 'o2'], 1 )
              )
            )

    def test_orderObjects(self):
        self._doCanonTestB( 'orderObjects',
              ( ( 'id', 'id',       ['o4', 'o3', 'o2', 'o1'], 3)
              , ( 'meta_type', '',  ['o1', 'o3', 'o2', 'o4'], 1)
              , ( 'meta_type', 'n', ['o4', 'o2', 'o3', 'o1'], 3)
              , ( 'position', 0,    ['o1', 'o2', 'o3', 'o4'], 0)
              , ( 'position', 1,    ['o4', 'o3', 'o2', 'o1'], 3)
              )
            )

    def test_getObjectPosition(self):
        self._doCanonTestA( 'getObjectPosition',
              ( ( 'o2', ['o1', 'o2', 'o3', 'o4'], 1)
              , ( 'o4', ['o1', 'o2', 'o3', 'o4'], 3)
              , ( 'n2', ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              )
            )

    def test_moveObjectToPosition(self):
        self._doCanonTestB( 'moveObjectToPosition',
              ( ( 'o2', 2, ['o1', 'o3', 'o2', 'o4'], 1)
              , ( 'o4', 2, ['o1', 'o2', 'o4', 'o3'], 1)
              , ( 'n2', 2, ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              )
            )

    def test_manage_renameObject(self):
        self._doCanonTestB( 'manage_renameObject',
              ( ( 'o2', 'n2', ['o1', 'n2', 'o3', 'o4'], None )
              , ( 'o3', 'n3', ['o1', 'o2', 'n3', 'o4'], None )
              )
            )

    def test_interface(self):
        from OFS.IOrderSupport import IOrderedContainer

        verifyClass(IOrderedContainer, OrderSupport)


def test_suite():
    return TestSuite( ( makeSuite(TestOrderSupport), ) )

if __name__ == '__main__':
    main(defaultTest='test_suite')
