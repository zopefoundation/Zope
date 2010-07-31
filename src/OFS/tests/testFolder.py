import unittest


class TestFolder(unittest.TestCase):

    def test_interfaces(self):
        from OFS.Folder import Folder
        from OFS.interfaces import IFolder
        from webdav.interfaces import IWriteLock
        from zope.interface.verify import verifyClass

        verifyClass(IFolder, Folder)
        verifyClass(IWriteLock, Folder)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestFolder),
        ))
