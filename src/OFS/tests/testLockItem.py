import unittest


class TestLockItem(unittest.TestCase):

    def test_interfaces(self):
        from zope.interface.verify import verifyClass

        from OFS.interfaces import ILockItem
        from OFS.LockItem import LockItem

        verifyClass(ILockItem, LockItem)
