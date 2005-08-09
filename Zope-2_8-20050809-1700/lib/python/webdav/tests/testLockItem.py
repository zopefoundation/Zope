import unittest


class TestLockItem(unittest.TestCase):

    def test_z2interfaces(self):
        from Interface.Verify import verifyClass
        from webdav.LockItem import LockItem
        from webdav.WriteLockInterface import LockItemInterface

        verifyClass(LockItemInterface, LockItem)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLockItem),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
