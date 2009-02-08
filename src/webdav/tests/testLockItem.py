import unittest


class TestLockItem(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.interfaces import ILockItem
        from webdav.LockItem import LockItem
        from zope.interface.verify import verifyClass

        verifyClass(ILockItem, LockItem)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLockItem),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
