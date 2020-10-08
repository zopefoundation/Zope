import unittest


class TestOrderedFolder(unittest.TestCase):

    def test_interfaces(self):
        from zope.interface.verify import verifyClass

        from OFS.interfaces import IOrderedContainer
        from OFS.interfaces import IOrderedFolder
        from OFS.interfaces import IWriteLock
        from OFS.OrderedFolder import OrderedFolder

        verifyClass(IOrderedContainer, OrderedFolder)
        verifyClass(IOrderedFolder, OrderedFolder)
        verifyClass(IWriteLock, OrderedFolder)
