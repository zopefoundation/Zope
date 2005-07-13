import unittest


class TestResource(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.interfaces import IDAVResource
        from webdav.interfaces import IWriteLock
        from webdav.Resource import Resource
        from zope.interface.verify import verifyClass

        verifyClass(IDAVResource, Resource)
        verifyClass(IWriteLock, Resource)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestResource),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
