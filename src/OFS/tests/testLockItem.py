import unittest


class TestLockItem(unittest.TestCase):

    def test_interfaces(self):
        from OFS.interfaces import ILockItem
        from OFS.LockItem import LockItem
        from zope.interface.verify import verifyClass

        verifyClass(ILockItem, LockItem)
