import unittest


class TestLockNullResource(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.interfaces import IWriteLock
        from webdav.NullResource import LockNullResource
        from zope.interface.verify import verifyClass

        verifyClass(IWriteLock, LockNullResource)


class TestNullResource(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.interfaces import IWriteLock
        from webdav.NullResource import NullResource
        from zope.interface.verify import verifyClass

        verifyClass(IWriteLock, NullResource)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLockNullResource),
        unittest.makeSuite(TestNullResource),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
