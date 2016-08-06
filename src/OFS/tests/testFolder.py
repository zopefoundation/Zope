import unittest


class TestFolder(unittest.TestCase):

    def test_interfaces(self):
        from OFS.Folder import Folder
        from OFS.interfaces import IFolder
        from OFS.interfaces import IWriteLock
        from zope.interface.verify import verifyClass

        verifyClass(IFolder, Folder)
        verifyClass(IWriteLock, Folder)
