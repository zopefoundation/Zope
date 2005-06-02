import unittest


class TestOrderedFolder(unittest.TestCase):

    def test_z2interfaces(self):
        from Interface.Verify import verifyClass
        from OFS.IOrderSupport import IOrderedContainer
        from OFS.OrderedFolder import OrderedFolder
        from webdav.WriteLockInterface import WriteLockInterface

        verifyClass(IOrderedContainer, OrderedFolder)
        verifyClass(WriteLockInterface, OrderedFolder)

    def test_z3interfaces(self):
        from OFS.interfaces import IOrderedContainer
        from OFS.interfaces import IOrderedFolder
        from OFS.OrderedFolder import OrderedFolder
        from webdav.interfaces import IWriteLock
        from zope.interface.verify import verifyClass

        verifyClass(IOrderedContainer, OrderedFolder, 1)
        verifyClass(IOrderedFolder, OrderedFolder, 1)
        verifyClass(IWriteLock, OrderedFolder, 1)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestOrderedFolder),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
