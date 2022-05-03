import os
import sys
import time
import unittest
from io import BytesIO

import OFS.Image
import Testing.testbrowser
import Testing.ZopeTestCase
import transaction
import Zope2
from Acquisition import aq_base
from OFS.Application import Application
from OFS.Cache import ZCM_MANAGERS
from OFS.Image import Pdata
from OFS.SimpleItem import SimpleItem
from Testing.makerequest import makerequest
from zExceptions import Redirect
from zope.component import adapter
from zope.datetime import rfc1123_date
from zope.lifecycleevent.interfaces import IObjectCreatedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse


here = os.path.dirname(os.path.abspath(__file__))
filedata = os.path.join(here, 'test.gif')

Zope2.startup_wsgi()


def makeConnection():
    import ZODB
    from ZODB.DemoStorage import DemoStorage

    s = DemoStorage()
    return ZODB.DB(s).open()


def aputrequest(file, content_type):
    resp = HTTPResponse(stdout=sys.stdout)
    environ = {}
    environ['SERVER_NAME'] = 'foo'
    environ['SERVER_PORT'] = '80'
    environ['REQUEST_METHOD'] = 'PUT'
    environ['CONTENT_TYPE'] = content_type
    req = HTTPRequest(stdin=file, environ=environ, response=resp)
    return req


class DummyCache:

    def __init__(self):
        self.clear()

    def ZCache_set(self, ob, data, view_name='', keywords=None,
                   mtime_func=None):
        self.set = (ob, data)

    def ZCache_get(self, ob, data, view_name='', keywords=None,
                   mtime_func=None):
        self.get = ob
        if self.si:
            return self.si

    def ZCache_invalidate(self, ob):
        self.invalidated = ob

    def clear(self):
        self.set = None
        self.get = None
        self.invalidated = None
        self.si = None

    def setStreamIterator(self, si):
        self.si = si


ADummyCache = DummyCache()


class DummyCacheManager(SimpleItem):
    def ZCacheManager_getCache(self):
        return ADummyCache


class EventCatcher:

    def __init__(self):
        self.created = []
        self.modified = []
        self.setUp()

    def setUp(self):
        from zope.component import provideHandler
        provideHandler(self.handleCreated)
        provideHandler(self.handleModified)

    def tearDown(self):
        from zope.component import getSiteManager
        getSiteManager().unregisterHandler(self.handleCreated)
        getSiteManager().unregisterHandler(self.handleModified)

    def reset(self):
        self.created = []
        self.modified = []

    @adapter(IObjectCreatedEvent)
    def handleCreated(self, event):
        if isinstance(event.object, OFS.Image.File):
            self.created.append(event)

    @adapter(IObjectModifiedEvent)
    def handleModified(self, event):
        if isinstance(event.object, OFS.Image.File):
            self.modified.append(event)


class FileTests(unittest.TestCase):
    content_type = 'application/octet-stream'
    factory = 'manage_addFile'

    def setUp(self):
        with open(filedata, 'rb') as fd:
            self.data = fd.read()
        self.connection = makeConnection()
        self.eventCatcher = EventCatcher()
        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            responseOut = self.responseOut = BytesIO()
            self.app = makerequest(self.root, stdout=responseOut)
            self.app.dcm = DummyCacheManager()
            factory = getattr(self.app, self.factory)
            factory('file',
                    file=self.data, content_type=self.content_type)
            self.app.file.ZCacheable_setManagerId('dcm')
            self.app.file.ZCacheable_setEnabled(enabled=1)
            setattr(self.app, ZCM_MANAGERS, ('dcm',))
            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one.
            transaction.commit()
        except Exception:
            transaction.abort()
            self.connection.close()
            raise
        transaction.begin()
        self.file = getattr(self.app, 'file')

        # Since we do the create here, let's test the events here too
        self.assertEqual(1, len(self.eventCatcher.created))
        self.assertTrue(
            aq_base(self.eventCatcher.created[0].object) is aq_base(self.file))

        self.assertEqual(1, len(self.eventCatcher.modified))
        self.assertTrue(
            aq_base(self.eventCatcher.created[0].object) is aq_base(self.file))

        self.eventCatcher.reset()

    def tearDown(self):
        del self.file
        transaction.abort()
        self.connection.close()
        del self.app
        del self.responseOut
        del self.root
        del self.connection
        ADummyCache.clear()
        self.eventCatcher.tearDown()

    def testViewImageOrFile(self):
        self.assertRaises(Redirect, self.file.view_image_or_file, 'foo')

    def testUpdateData(self):
        self.file.update_data(b'foo')
        self.assertEqual(self.file.size, 3)
        self.assertEqual(self.file.data, b'foo')
        self.assertTrue(ADummyCache.invalidated)
        self.assertTrue(ADummyCache.set)

    def testReadData(self):
        s = b'a' * (2 << 16)
        data, size = self.file._read_data(BytesIO(s))
        self.assertIsInstance(data, Pdata)
        self.assertEqual(bytes(data), s)
        self.assertEqual(len(s), len(bytes(data)))
        self.assertEqual(len(s), size)

    def testBigPdata(self):
        # Test that a big enough string is split into several Pdata
        # From a file
        s = b'a' * (1 << 16) * 3
        data, size = self.file._read_data(BytesIO(s))
        self.assertNotEqual(data.next, None)
        # From a string
        data, size = self.file._read_data(s)
        self.assertNotEqual(data.next, None)

    def testManageEditWithFileData(self):
        self.file.manage_edit('foobar', 'text/plain', filedata=b'ASD')
        self.assertEqual(self.file.title, 'foobar')
        self.assertEqual(self.file.content_type, 'text/plain')
        self.assertTrue(ADummyCache.invalidated)
        self.assertTrue(ADummyCache.set)
        self.assertEqual(1, len(self.eventCatcher.modified))
        self.assertTrue(self.eventCatcher.modified[0].object is self.file)

    def testManageEditWithoutFileData(self):
        self.file.manage_edit('foobar', 'text/plain')
        self.assertEqual(self.file.title, 'foobar')
        self.assertEqual(self.file.content_type, 'text/plain')
        self.assertTrue(ADummyCache.invalidated)
        self.assertEqual(1, len(self.eventCatcher.modified))
        self.assertTrue(self.eventCatcher.modified[0].object is self.file)

    def testManageUpload(self):
        f = BytesIO(b'jammyjohnson')
        self.file.manage_upload(f)
        self.assertEqual(self.file.data, b'jammyjohnson')
        self.assertEqual(self.file.content_type, 'application/octet-stream')
        self.assertEqual(1, len(self.eventCatcher.modified))
        self.assertTrue(self.eventCatcher.modified[0].object is self.file)

    def testManageUploadWithoutFileData(self):
        self.file.manage_upload()
        self.assertEqual(0, len(self.eventCatcher.modified))

    def testIfModSince(self):
        now = time.time()
        e = {'SERVER_NAME': 'foo',
             'SERVER_PORT': '80',
             'REQUEST_METHOD': 'GET'}

        # not modified since
        t_notmod = rfc1123_date(now)
        e['HTTP_IF_MODIFIED_SINCE'] = t_notmod
        out = BytesIO()
        resp = HTTPResponse(stdout=out)
        req = HTTPRequest(sys.stdin, e, resp)
        data = self.file.index_html(req, resp)
        self.assertEqual(resp.getStatus(), 304)
        self.assertEqual(data, b'')

        # modified since
        t_mod = rfc1123_date(now - 100)
        e['HTTP_IF_MODIFIED_SINCE'] = t_mod
        out = BytesIO()
        resp = HTTPResponse(stdout=out)
        req = HTTPRequest(sys.stdin, e, resp)
        data = self.file.index_html(req, resp)
        self.assertEqual(resp.getStatus(), 200)
        self.assertEqual(data, bytes(self.file.data))

    def testPUT(self):
        s = b'# some python\n'

        # with content type
        data = BytesIO(s)
        req = aputrequest(data, 'text/x-python')
        req.processInputs()
        self.file.PUT(req, req.RESPONSE)

        self.assertEqual(self.file.content_type, 'text/x-python')
        self.assertEqual(self.file.data, s)

        # without content type
        data.seek(0)
        req = aputrequest(data, '')
        req.processInputs()
        self.file.PUT(req, req.RESPONSE)

        self.assertEqual(self.file.content_type, 'text/x-python')
        self.assertEqual(self.file.data, s)

    def testIndexHtmlWithPdata(self):
        self.file.manage_upload(b'a' * (2 << 16))  # 128K
        self.file.index_html(self.app.REQUEST, self.app.REQUEST.RESPONSE)
        self.assertTrue(self.app.REQUEST.RESPONSE._wrote)

    def testIndexHtmlWithString(self):
        self.file.manage_upload(b'a' * 100)  # 100 bytes
        self.file.index_html(self.app.REQUEST, self.app.REQUEST.RESPONSE)
        self.assertTrue(not self.app.REQUEST.RESPONSE._wrote)

    def testPrincipiaSearchSource_not_text(self):
        data = ''.join([chr(x) for x in range(256)])
        data = data.encode('utf-8')
        self.file.manage_edit('foobar', 'application/octet-stream',
                              filedata=data)
        self.assertEqual(self.file.PrincipiaSearchSource(), b'')

    def testPrincipiaSearchSource_text(self):
        self.file.manage_edit('foobar', 'text/plain',
                              filedata=b'Now is the time for all good men to '
                                       b'come to the aid of the Party.')
        self.assertTrue(b'Party' in self.file.PrincipiaSearchSource())

    def test_manage_DAVget_binary(self):
        self.assertEqual(self.file.manage_DAVget(), self.data)

    def test_manage_DAVget_text(self):
        text = (b'Now is the time for all good men to '
                b'come to the aid of the Party.')
        self.file.manage_edit('foobar', 'text/plain', filedata=text)
        self.assertEqual(self.file.manage_DAVget(), text)

    def test_interfaces(self):
        from OFS.Image import File
        from OFS.interfaces import IWriteLock
        from zope.interface.verify import verifyClass
        from ZPublisher.HTTPRangeSupport import HTTPRangeInterface

        verifyClass(HTTPRangeInterface, File)
        verifyClass(IWriteLock, File)

    def testUnicode(self):
        val = 'some unicode string here'

        self.assertRaises(TypeError, self.file.update_data,
                          data=val, content_type='text/plain')

    def test__str__returns_native_string(self):
        small_data = b'small data'
        self.file.manage_upload(file=small_data)
        self.assertEqual(str(self.file), small_data.decode())

        # Make sure Pdata contents are handled correctly
        big_data = b'a' * (2 << 16)
        self.file.manage_upload(file=big_data)
        self.assertEqual(str(self.file), big_data.decode())


class ImageTests(FileTests):
    content_type = 'image/gif'
    factory = 'manage_addImage'

    def testUpdateData(self):
        self.file.update_data(self.data)
        self.assertEqual(self.file.size, len(self.data))
        self.assertEqual(self.file.data, self.data)
        self.assertEqual(self.file.width, 16)
        self.assertEqual(self.file.height, 16)
        self.assertTrue(ADummyCache.invalidated)
        self.assertTrue(ADummyCache.set)

    def testTag(self):
        tag_fmt = ('<img src="http://nohost/file" '
                   'alt="%s" title="%s" height="16" width="16" />')
        self.assertEqual(self.file.tag(), (tag_fmt % ('', '')))
        self.file.manage_changeProperties(title='foo')
        self.assertEqual(self.file.tag(), (tag_fmt % ('', 'foo')))
        self.file.manage_changeProperties(alt='bar')
        self.assertEqual(self.file.tag(), (tag_fmt % ('bar', 'foo')))

    testStr = testTag

    def test__str__returns_native_string(self):
        small_data = b'small data'
        self.file.manage_upload(file=small_data)
        self.assertIsInstance(str(self.file), str)

        # Make sure Pdata contents are handled correctly
        big_data = b'a' * (2 << 16)
        self.file.manage_upload(file=big_data)
        self.assertIsInstance(str(self.file), str)

    def testViewImageOrFile(self):
        request = self.app.REQUEST
        response = request.RESPONSE
        result = self.file.index_html(request, response)
        self.assertEqual(result, self.data)

    def test_interfaces(self):
        from OFS.Image import Image
        from OFS.interfaces import IWriteLock
        from zope.interface.verify import verifyClass

        verifyClass(IWriteLock, Image)

    def test_text_representation_is_tag(self):
        self.assertEqual(str(self.file),
                         '<img src="http://nohost/file"'
                         ' alt="" title="" height="16" width="16" />')


class FileEditTests(Testing.ZopeTestCase.FunctionalTestCase):
    """Browser testing ..Image.File"""

    def setUp(self):
        super().setUp()
        uf = self.app.acl_users
        uf.userFolderAddUser('manager', 'manager_pass', ['Manager'], [])
        self.app.manage_addFile('file')

        transaction.commit()
        self.browser = Testing.testbrowser.Browser()
        self.browser.login('manager', 'manager_pass')

    def test_Image__manage_main__1(self):
        """It shows the content of text files as text."""
        self.app.file.update_data('hällo'.encode())
        self.browser.open('http://localhost/file/manage_main')
        text = self.browser.getControl(name='filedata:text').value
        self.assertEqual(text, 'hällo')

    def test_Image__manage_main__3(self):
        """It shows an error message if the file content cannot be decoded."""
        self.app.file.update_data('hällo'.encode('latin-1'))
        self.browser.open('http://localhost/file/manage_main')
        self.assertIn(
            "The file could not be decoded with 'utf-8'.",
            self.browser.contents)

    def test_Image__manage_upload__1(self):
        """It uploads a file, replaces the content and sets content type."""
        self.browser.open('http://localhost/file/manage_main')
        self.browser.getControl(name='file').add_file(
            b'test text file', 'text/plain', 'TestFile.txt')
        self.browser.getControl('Upload File').click()
        self.assertIn('Saved changes', self.browser.contents)
        self.assertEqual(
            self.browser.getControl('Content Type').value, 'text/plain')
        text = self.browser.getControl(name='filedata:text').value
        self.assertEqual(text, 'test text file')

    def test_Image__manage_edit__1(self):
        """It it possible to change the file's content via browser."""
        self.browser.open('http://localhost/file/manage_main')
        text_1 = self.browser.getControl(name='filedata:text').value
        self.assertEqual(text_1, '')
        self.browser.getControl(name='filedata:text').value = 'hällo'
        self.browser.getControl('Save Changes').click()
        self.assertIn('Saved changes', self.browser.contents)
        text_2 = self.browser.getControl(name='filedata:text').value
        self.assertEqual(text_2, 'hällo')
