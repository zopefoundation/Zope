import unittest

class DTMLDocumentTests(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.DTMLDocument import DTMLDocument
        return DTMLDocument

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_class_conforms_to_IWriteLock(self):
        from zope.interface.verify import verifyClass
        from webdav.interfaces import IWriteLock
        verifyClass(IWriteLock, self._getTargetClass())


class FactoryTests(unittest.TestCase):

    def test_defaults_no_standard_html_header(self):
        # see LP #496961
        from OFS.DTMLDocument import addDTMLDocument
        from OFS.DTMLDocument import DTMLDocument
        dispatcher = DummyDispatcher()
        addDTMLDocument(dispatcher, 'id')
        method = dispatcher._set['id']
        self.assertTrue(isinstance(method, DTMLDocument))
        self.assertFalse('standard_html_header' in method.read())
        self.assertFalse('standard_html_footer' in method.read())


class DummyDispatcher:

    def __init__(self):
        self._set = {}

    def _setObject(self, key, value):
        self._set[key] = value

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(DTMLDocumentTests),
        unittest.makeSuite(FactoryTests),
        ))
