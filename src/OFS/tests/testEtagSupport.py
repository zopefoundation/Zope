import unittest


class TestEtagSupport(unittest.TestCase):

    def test_interfaces(self):
        from zope.interface.verify import verifyClass
        from OFS.EtagSupport import EtagBaseInterface
        from OFS.EtagSupport import EtagSupport

        verifyClass(EtagBaseInterface, EtagSupport)
