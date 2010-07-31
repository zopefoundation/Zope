import unittest


class TestFTPInterface(unittest.TestCase):

    def test_interfaces(self):
        from OFS.interfaces import IFTPAccess
        from OFS.FTPInterface import FTPInterface
        from zope.interface.verify import verifyClass

        verifyClass(IFTPAccess, FTPInterface)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestFTPInterface),
        ))
