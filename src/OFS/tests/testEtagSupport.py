import unittest


class TestEtagSupport(unittest.TestCase):

    def test_interfaces(self):
        from OFS.EtagSupport import EtagBaseInterface
        from OFS.EtagSupport import EtagSupport
        from zope.interface.verify import verifyClass

        verifyClass(EtagBaseInterface, EtagSupport)
