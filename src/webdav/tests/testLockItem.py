import unittest


class TestLockItem(unittest.TestCase):

    def test_interfaces(self):
        from webdav.interfaces import ILockItem
        from webdav.LockItem import LockItem
        from zope.interface.verify import verifyClass

        verifyClass(ILockItem, LockItem)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLockItem),
        ))
