import unittest


class TestPersistent(unittest.TestCase):

    def test_interfaces(self):
        from App.interfaces import IPersistentExtra
        from Persistence import Persistent
        from zope.interface.verify import verifyClass
        from App.PersistentExtra import patchPersistent

        patchPersistent()
        verifyClass(IPersistentExtra, Persistent)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestPersistent),
        ))
