# -*- coding: utf-8 -*-
import io
import unittest

import Testing.testbrowser
import Testing.ZopeTestCase
import zExceptions
import Zope2.App.zcml
from Testing.makerequest import makerequest


def _lock_item(item):
    from OFS.LockItem import LockItem
    from AccessControl.SpecialUsers import nobody
    item.wl_setLock('token', LockItem(nobody, token='token'))


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

    def test_manage_upload__bytes(self):
        """It stores uploaded bytes as a native str."""
        doc = self._makeOne()
        data = u'bÿtës'.encode('utf-8')
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
        data = io.StringIO(u'bÿtës')
        doc.manage_upload(data)
        self.assertIsInstance(doc.read(), str)
        self.assertEqual(doc.read(), 'bÿtës')

    def test_manage_upload__BytesIO(self):
        """It stores BytesIO contents as a native str."""
        doc = self._makeOne()
        data = io.BytesIO(u'bÿtës'.encode('utf-8'))
        doc.manage_upload(data)
        self.assertEqual(doc.read(), 'bÿtës')
        self.assertIsInstance(doc.read(), str)

    def test_manage_upload__Locked(self):
        """It raises an exception if the object is locked."""
        doc = self._makeOne()
        _lock_item(doc)
        with self.assertRaises(zExceptions.ResourceLockedError) as err:
            doc.manage_upload()
        self.assertEqual('This DTML Method is locked.', str(err.exception))

    def test_manage_edit__Locked(self):
        """It raises an exception if the object is locked."""
        doc = self._makeOne()
        _lock_item(doc)
        with self.assertRaises(zExceptions.ResourceLockedError) as err:
            doc.manage_edit('data', 'title')
        self.assertEqual('This DTML Method is locked.', str(err.exception))

    def test_manage_edit__invalid_code(self):
        """It raises an exception if the code is invalid."""
        from DocumentTemplate.DT_Util import ParseError
        doc = self._makeOne()
        with self.assertRaises(ParseError) as err:
            doc.manage_edit('</dtml-let>', 'title')
        self.assertEqual(
            'unexpected end tag, for tag </dtml-let>, on line 1 of <string>',
            str(err.exception))

    def test__call__missing_encoding_old_instances(self):
        """ Existing DTML methods have no "encoding" attribute """
        from OFS.Folder import Folder
        client = makerequest(Folder('client'))
        response = client.REQUEST['RESPONSE']
        doc = self._makeOne(source_string='foo')

        # In order to test the issue I need to delete the "encoding" attribute
        # that existing instances did not have.
        del doc.encoding

        self.assertEqual(doc(client=client, RESPONSE=response), u'foo')


class DTMLMethodBrowserTests(Testing.ZopeTestCase.FunctionalTestCase):
    """Browser testing ..OFS.DTMLMethod"""

    def setUp(self):
        from OFS.DTMLMethod import addDTMLMethod
        super(DTMLMethodBrowserTests, self).setUp()

        Zope2.App.zcml.load_site(force=True)

        uf = self.app.acl_users
        uf.userFolderAddUser('manager', 'manager_pass', ['Manager'], [])
        addDTMLMethod(self.app, 'dtml_meth')

        self.browser = Testing.testbrowser.Browser()
        self.browser.login('manager', 'manager_pass')
        self.browser.open('http://localhost/dtml_meth/manage_main')

    def test_manage_upload__Locked__REQUEST(self):
        """It renders an error message if the object is locked."""
        _lock_item(self.app.dtml_meth)
        file_contents = b'<dtml-var "Hello!">'
        self.browser.getControl('file').add_file(
            file_contents, 'text/plain', 'hello.dtml')
        self.browser.getControl('Upload File').click()
        self.assertIn('This DTML Method is locked.', self.browser.contents)
        self.assertNotEqual(
            self.browser.getControl(name='data:text').value, file_contents)

    def test_manage_upload__no_file(self):
        """It renders an error message if no file is uploaded."""
        self.browser.getControl('Upload File').click()
        self.assertIn('No file specified', self.browser.contents)

    def test_manage_upload__file_uploaded(self):
        """It renders a success message if a file is uploaded."""
        file_contents = b'<dtml-var title_or_id>'
        self.browser.getControl('file').add_file(
            file_contents, 'text/plain', 'hello.dtml')
        self.browser.getControl('Upload File').click()
        self.assertIn('Content uploaded.', self.browser.contents)
        self.assertEqual(
            self.browser.getControl(name='data:text').value,
            file_contents.decode())

    def test_manage_edit__ParseError(self):
        """It renders an error message if the DTML code is invalid."""
        code = '</dtml-let>'
        self.browser.getControl(name='data:text').value = code
        self.browser.getControl('Save').click()
        self.assertIn(
            'unexpected end tag, for tag &lt;/dtml-let&gt;,'
            ' on line 1 of dtml_meth', self.browser.contents)
        # But the value gets stored:
        self.assertEqual(self.browser.getControl(name='data:text').value, code)

    def test_manage_edit__success(self):
        """It renders a success message if the DTML code is valid."""
        code = '<dtml-var title_or_id>'
        self.browser.getControl(name='data:text').value = code
        self.browser.getControl('Save').click()
        self.assertIn('Saved changes.', self.browser.contents)
        self.assertEqual(self.browser.getControl(name='data:text').value, code)


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


class DummyDispatcher(object):

    def __init__(self):
        self._set = {}

    def _setObject(self, key, value):
        self._set[key] = value
