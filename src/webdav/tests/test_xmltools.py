import unittest

class TestNode(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.xmltools import Node
        return Node

    def _makeOne(self, wrapped):
        klass = self._getTargetClass()
        return klass(wrapped)

    def test_remove_namespace_attrs(self):
        """ A method added in Zope 2.11 which removes any attributes
        which appear to be XML namespace declarations """
        class DummyMinidomNode:
            def __init__(self):
                self.attributes = {'xmlns:foo':'foo', 'xmlns':'bar', 'a':'b'}
            def hasAttributes(self):
                return True
            def removeAttribute(self, name):
                del self.attributes[name]

        wrapped = DummyMinidomNode()
        node = self._makeOne(wrapped)
        node.remove_namespace_attrs()
        self.assertEqual(wrapped.attributes, {'a':'b'})


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestNode),
        ))
