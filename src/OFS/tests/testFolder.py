import unittest


class TestFolder(unittest.TestCase):

    def test_interfaces(self):
        from zope.interface.verify import verifyClass

        from OFS.Folder import Folder
        from OFS.interfaces import IFolder
        from OFS.interfaces import IWriteLock

        verifyClass(IFolder, Folder)
        verifyClass(IWriteLock, Folder)
