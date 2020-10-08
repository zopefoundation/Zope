import unittest


class TestCollection(unittest.TestCase):

    def test_interfaces(self):
        from zope.interface.verify import verifyClass

        from webdav.Collection import Collection
        from webdav.interfaces import IDAVCollection

        verifyClass(IDAVCollection, Collection)
