import unittest


class DTMLMethodTests(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.DTMLMethod import DTMLMethod
        return DTMLMethod

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_class_conforms_to_IWriteLock(self):
        from zope.interface.verify import verifyClass
        from OFS.interfaces import IWriteLock
        verifyClass(IWriteLock, self._getTargetClass())

    def test_edit_taintedstring(self):
        from AccessControl.tainted import TaintedString
        doc = self._makeOne()
        self.assertEqual(doc.read(), '')
        data = TaintedString('hello<br/>')

        doc.manage_edit(data, 'title')
        self.assertEqual(doc.read(), 'hello&lt;br/&gt;')


class FactoryTests(unittest.TestCase):

    def test_defaults_no_standard_html_header(self):
        # see LP #496961
        from OFS.DTMLMethod import addDTMLMethod
        from OFS.DTMLMethod import DTMLMethod
        dispatcher = DummyDispatcher()
        addDTMLMethod(dispatcher, 'id')
        method = dispatcher._set['id']
        self.assertIsInstance(method, DTMLMethod)
        self.assertFalse('standard_html_header' in method.read())
        self.assertFalse('standard_html_footer' in method.read())


class DummyDispatcher:

    def __init__(self):
        self._set = {}

    def _setObject(self, key, value):
        self._set[key] = value
