import io
import unittest

from Testing.makerequest import makerequest


class DTMLDocumentTests(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.DTMLDocument import DTMLDocument
        return DTMLDocument

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_class_conforms_to_IWriteLock(self):
        from OFS.interfaces import IWriteLock
        from zope.interface.verify import verifyClass
        verifyClass(IWriteLock, self._getTargetClass())

    def test_manage_upload__bytes(self):
        """It stores uploaded bytes as a native str."""
        doc = self._makeOne()
        data = 'bÿtës'.encode()
        self.assertIsInstance(data, bytes)
        doc.manage_upload(data)
        self.assertEqual(doc.read(), 'bÿtës')
        self.assertIsInstance(doc.read(), str)

    def test_manage_upload__str(self):
        """It stores an uploaded str as a native str."""
        doc = self._makeOne()
        data = 'bÿtës'
        doc.manage_upload(data)
        self.assertEqual(doc.read(), 'bÿtës')
        self.assertIsInstance(doc.read(), str)

    def test_manage_upload__StringIO(self):
        """It stores StringIO contents as a native str."""
        doc = self._makeOne()
        data = io.StringIO('bÿtës')
        doc.manage_upload(data)
        self.assertIsInstance(doc.read(), str)
        self.assertEqual(doc.read(), 'bÿtës')

    def test_manage_upload__BytesIO(self):
        """It stores BytesIO contents as a native str."""
        doc = self._makeOne()
        data = io.BytesIO('bÿtës'.encode())
        doc.manage_upload(data)
        self.assertEqual(doc.read(), 'bÿtës')
        self.assertIsInstance(doc.read(), str)

    def test__call__missing_encoding_old_instances(self):
        """ Existing DTML documents have no "encoding" attribute """
        from OFS.Folder import Folder
        client = makerequest(Folder('client'))
        response = client.REQUEST['RESPONSE']
        doc = self._makeOne(source_string='foo')

        # In order to test the issue I need to delete the "encoding" attribute
        # that existing instances did not have.
        del doc.encoding

        self.assertEqual(doc(client=client, RESPONSE=response), 'foo')


class FactoryTests(unittest.TestCase):

    def test_defaults_no_standard_html_header(self):
        # see LP #496961
        from OFS.DTMLDocument import DTMLDocument
        from OFS.DTMLDocument import addDTMLDocument
        dispatcher = DummyDispatcher()
        addDTMLDocument(dispatcher, 'id')
        method = dispatcher._set['id']
        self.assertIsInstance(method, DTMLDocument)
        self.assertFalse('standard_html_header' in method.read())
        self.assertFalse('standard_html_footer' in method.read())


class DummyDispatcher:

    def __init__(self):
        self._set = {}

    def _setObject(self, key, value):
        self._set[key] = value
