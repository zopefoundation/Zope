import unittest
import Testing
import Zope2
Zope2.startup()


class TestResource(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.interfaces import IDAVResource
        from webdav.Resource import Resource
        from zope.interface.verify import verifyClass

        verifyClass(IDAVResource, Resource, 1)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestResource),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
