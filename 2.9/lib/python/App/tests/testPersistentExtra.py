import unittest
import Testing
import Zope2
Zope2.startup()


class TestPersistentUtil(unittest.TestCase):

    def test_z3interfaces(self):
        from App.interfaces import IPersistentExtra
        from App.PersistentExtra import PersistentUtil
        from zope.interface.verify import verifyClass

        verifyClass(IPersistentExtra, PersistentUtil)


class TestPersistent(unittest.TestCase):

    def test_z3interfaces(self):
        from App.interfaces import IPersistentExtra
        from Persistence import Persistent
        from zope.interface.verify import verifyClass

        verifyClass(IPersistentExtra, Persistent)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestPersistentUtil),
        unittest.makeSuite(TestPersistent),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
