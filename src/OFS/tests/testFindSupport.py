import unittest


class TestFindSupport(unittest.TestCase):

    def test_interfaces(self):
        from OFS.interfaces import IFindSupport
        from OFS.FindSupport import FindSupport
        from zope.interface.verify import verifyClass

        verifyClass(IFindSupport, FindSupport)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestFindSupport),
        ))
