import unittest


class TestCollection(unittest.TestCase):

    def test_interfaces(self):
        from webdav.Collection import Collection
        from webdav.interfaces import IDAVCollection
        from zope.interface.verify import verifyClass

        verifyClass(IDAVCollection, Collection)
