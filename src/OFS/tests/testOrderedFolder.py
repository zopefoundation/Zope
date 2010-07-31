import unittest


class TestOrderedFolder(unittest.TestCase):

    def test_interfaces(self):
        from OFS.interfaces import IOrderedContainer
        from OFS.interfaces import IOrderedFolder
        from OFS.OrderedFolder import OrderedFolder
        from webdav.interfaces import IWriteLock
        from zope.interface.verify import verifyClass

        verifyClass(IOrderedContainer, OrderedFolder)
        verifyClass(IOrderedFolder, OrderedFolder)
        verifyClass(IWriteLock, OrderedFolder)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestOrderedFolder),
        ))
