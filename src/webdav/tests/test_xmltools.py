import unittest

class NodeTests(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.xmltools import Node
        return Node

    def _makeOne(self, wrapped):
        return self._getTargetClass()(wrapped)

    def test_remove_namespace_attrs(self):
        class DummyMinidomNode(object):
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


class XmlParserTests(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.xmltools import XmlParser
        return XmlParser

    def _makeOne(self):
        return self._getTargetClass()()

    def test_parse_rejects_entities(self):
        XML = '\n'.join([
            '<!DOCTYPE dt_test [',
            '<!ENTITY entity "1234567890" >',
            ']>',
            '<test>&entity;</test>'
        ])
        parser = self._makeOne()
        self.assertRaises(ValueError, parser.parse, XML)

    def test_parse_rejects_doctype_wo_entities(self):
        XML = '\n'.join([
            '<!DOCTYPE dt_test []>',
            '<test/>'
        ])
        parser = self._makeOne()
        self.assertRaises(ValueError, parser.parse, XML)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(NodeTests),
        unittest.makeSuite(XmlParserTests),
    ))
