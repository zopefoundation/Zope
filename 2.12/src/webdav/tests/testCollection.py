import unittest


class TestCollection(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.Collection import Collection
        from webdav.interfaces import IDAVCollection
        from zope.interface.verify import verifyClass

        verifyClass(IDAVCollection, Collection)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestCollection),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
