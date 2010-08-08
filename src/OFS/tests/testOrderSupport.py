import unittest

from OFS.CopySupport import CopySource
from OFS.ObjectManager import ObjectManager


class DummyObject(CopySource):
    def __init__(self, id, meta_type):
        self.id = id
        self.meta_type = meta_type
    def cb_isMoveable(self):
        return 1
    def manage_afterAdd(self, item, container):
        return
    def manage_beforeDelete(self, item, container):
        return
    manage_afterAdd.__five_method__ = True
    manage_beforeDelete.__five_method__ = True
    def wl_isLocked(self):
        return 0


class TestOrderSupport(unittest.TestCase):

    def _makeOne(self):
        from OFS.OrderSupport import OrderSupport

        class OrderedObjectManager(OrderSupport, ObjectManager):
            # disable permission verification
            def _verifyObjectPaste(self, object, validate_src=1):
                return

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

    def test_interfaces(self):
        from OFS.interfaces import IOrderedContainer
        from OFS.OrderSupport import OrderSupport
        from zope.interface.verify import verifyClass

        verifyClass(IOrderedContainer, OrderSupport)

    def _doCanonTest(self, methodname, table):
        for args, order, rval in table:
            f = self._makeOne()
            method = getattr(f, methodname)
            if rval == 'ValueError':
                self.assertRaises( ValueError, method, *args )
            else:
                self.assertEqual( method(*args), rval )
            self.assertEqual( f.objectIds(), order )

    def test_moveObjectsUp(self):
        self._doCanonTest( 'moveObjectsUp',
              ( ( ( 'o4', 1 ),         ['o1', 'o2', 'o4', 'o3'], 1 )
              , ( ( 'o4', 2 ),         ['o1', 'o4', 'o2', 'o3'], 1 )
              , ( ( ('o1', 'o3'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o1', 'o3'), 9 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), 1 ), ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o1', 'o2', 'o3', 'o4') ),
                                       ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o2', 'o3', 'o4') ),
                                       ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), 1 ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ( ('o3', 'o1'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsDown(self):
        self._doCanonTest( 'moveObjectsDown',
              ( ( ( 'o1', 1 ),         ['o2', 'o1', 'o3', 'o4'], 1 )
              , ( ( 'o1', 2 ),         ['o2', 'o3', 'o1', 'o4'], 1 )
              , ( ( ('o2', 'o4'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o4'), 9 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), 1 ), ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o1', 'o2', 'o3', 'o4') ),
                                       ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), 1, ('o1', 'o2', 'o3') ),
                                       ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), 1 ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ( ('o4', 'o2'), 1 ), ['o1', 'o3', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsToTop(self):
        self._doCanonTest( 'moveObjectsToTop',
              ( ( ( 'o4', ),         ['o4', 'o1', 'o2', 'o3'], 1 )
              , ( ( ('o1', 'o3'), ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), ), ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), ('o1', 'o2', 'o3', 'o4') ),
                                     ['o2', 'o3', 'o1', 'o4'], 2 )
              , ( ( ('o2', 'o3'), ('o2', 'o3', 'o4') ),
                                     ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ( ('o3', 'o1'), ), ['o3', 'o1', 'o2', 'o4'], 1 )
              )
            )

    def test_moveObjectsToBottom(self):
        self._doCanonTest( 'moveObjectsToBottom',
              ( ( ( 'o1', ),         ['o2', 'o3', 'o4', 'o1'], 1 )
              , ( ( ('o2', 'o4'), ), ['o1', 'o3', 'o2', 'o4'], 1 )
              , ( ( ('o2', 'o3'), ), ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), ('o1', 'o2', 'o3', 'o4') ),
                                     ['o1', 'o4', 'o2', 'o3'], 2 )
              , ( ( ('o2', 'o3'), ('o1', 'o2', 'o3') ),
                                     ['o1', 'o2', 'o3', 'o4'], 0 )
              , ( ( ('n2', 'o3'), ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              , ( ( ('o4', 'o2'), ), ['o1', 'o3', 'o4', 'o2'], 1 )
              )
            )

    def test_orderObjects(self):
        self._doCanonTest( 'orderObjects',
              ( ( ( 'id', 'id' ),       ['o4', 'o3', 'o2', 'o1'], 3)
              , ( ( 'meta_type', '' ),  ['o1', 'o3', 'o2', 'o4'], 1)
              , ( ( 'meta_type', 'n' ), ['o4', 'o2', 'o3', 'o1'], 3)
              , ( ( 'position', 0 ),    ['o1', 'o2', 'o3', 'o4'], 0)
              , ( ( 'position', 1 ),    ['o4', 'o3', 'o2', 'o1'], 3)
              )
            )

    def test_getObjectPosition(self):
        self._doCanonTest( 'getObjectPosition',
              ( ( ( 'o2', ), ['o1', 'o2', 'o3', 'o4'], 1)
              , ( ( 'o4', ), ['o1', 'o2', 'o3', 'o4'], 3)
              , ( ( 'n2', ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              )
            )

    def test_moveObjectToPosition(self):
        self._doCanonTest( 'moveObjectToPosition',
              ( ( ( 'o2', 2 ), ['o1', 'o3', 'o2', 'o4'], 1)
              , ( ( 'o4', 2 ), ['o1', 'o2', 'o4', 'o3'], 1)
              , ( ( 'n2', 2 ), ['o1', 'o2', 'o3', 'o4'], 'ValueError')
              )
            )

    def test_manage_renameObject(self):
        self._doCanonTest( 'manage_renameObject',
              ( ( ( 'o2', 'n2' ), ['o1', 'n2', 'o3', 'o4'], None )
              , ( ( 'o3', 'n3' ), ['o1', 'o2', 'n3', 'o4'], None )
              )
            )

    def test_tpValues(self):
        f = self._makeOne()
        f.o2.isPrincipiaFolderish = True
        f.o3.isPrincipiaFolderish = True
        f.o4.isPrincipiaFolderish = True
        self.assertEqual( f.tpValues(), [f.o2, f.o3, f.o4] )

        f.setDefaultSorting('meta_type', False)
        self.assertEqual( f.tpValues(), [f.o3, f.o2, f.o4] )

        f.setDefaultSorting('position', True)
        self.assertEqual( f.tpValues(), [f.o4, f.o3, f.o2] )


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestOrderSupport),
        ))
