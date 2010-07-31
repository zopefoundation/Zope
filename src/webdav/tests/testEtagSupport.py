import unittest


class TestEtagSupport(unittest.TestCase):

    def test_interfaces(self):
        from zope.interface.verify import verifyClass
        from webdav.EtagSupport import EtagBaseInterface
        from webdav.EtagSupport import EtagSupport

        verifyClass(EtagBaseInterface, EtagSupport)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestEtagSupport),
        ))
