import unittest

import Zope2

import os
import sys
import time
from io import BytesIO

from Acquisition import aq_base

from OFS.Application import Application
from OFS.Image import Pdata
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from App.Common import rfc1123_date
from Testing.makerequest import makerequest
from zExceptions import Redirect
import transaction

import OFS.Image

from zope.component import adapter
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

here = os.path.dirname(os.path.abspath(__file__))
imagedata = os.path.join(here, 'test.gif')
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


class EventCatcher(object):

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
    data = open(filedata, 'rb').read()
    content_type = 'application/octet-stream'
    factory = 'manage_addFile'

    def setUp(self):
        self.connection = makeConnection()
        self.eventCatcher = EventCatcher()
        try:
            r = self.connection.root()
            a = Application()
            r['Application'] = a
            self.root = a
            responseOut = self.responseOut = BytesIO()
            self.app = makerequest(self.root, stdout=responseOut)
            factory = getattr(self.app, self.factory)
            factory('file',
                    file=self.data, content_type=self.content_type)
            # Hack, we need a _p_mtime for the file, so we make sure that it
            # has one.
            transaction.commit()
        except Exception:
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
        self.eventCatcher.tearDown()

    def testViewImageOrFile(self):
        self.assertRaises(Redirect, self.file.view_image_or_file, 'foo')

    def testUpdateData(self):
        self.file.update_data('foo')
        self.assertEqual(self.file.size, 3)
        self.assertEqual(self.file.data, 'foo')

    def testReadData(self):
        s = "a" * (2 << 16)
        f = BytesIO(s)
        data, size = self.file._read_data(f)
        self.assertTrue(isinstance(data, Pdata))
        self.assertEqual(str(data), s)
        self.assertEqual(len(s), len(str(data)))
        self.assertEqual(len(s), size)

    def testBigPdata(self):
        # Test that a big enough string is split into several Pdata
        # From a file
        s = "a" * (1 << 16) * 3
        data, size = self.file._read_data(BytesIO(s))
        self.assertNotEqual(data.next, None)
        # From a string
        data, size = self.file._read_data(s)
        self.assertNotEqual(data.next, None)

    def testManageEditWithFileData(self):
        self.file.manage_edit('foobar', 'text/plain', filedata='ASD')
        self.assertEqual(self.file.title, 'foobar')
        self.assertEqual(self.file.content_type, 'text/plain')
        self.assertEqual(1, len(self.eventCatcher.modified))
        self.assertTrue(self.eventCatcher.modified[0].object is self.file)

    def testManageEditWithoutFileData(self):
        self.file.manage_edit('foobar', 'text/plain')
        self.assertEqual(self.file.title, 'foobar')
        self.assertEqual(self.file.content_type, 'text/plain')
        self.assertEqual(1, len(self.eventCatcher.modified))
        self.assertTrue(self.eventCatcher.modified[0].object is self.file)

    def testManageUpload(self):
        f = BytesIO('jammyjohnson')
        self.file.manage_upload(f)
        self.assertEqual(self.file.data, 'jammyjohnson')
        self.assertEqual(self.file.content_type, 'application/octet-stream')
        self.assertEqual(1, len(self.eventCatcher.modified))
        self.assertTrue(self.eventCatcher.modified[0].object is self.file)

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
        self.assertEqual(data, '')

        # modified since
        t_mod = rfc1123_date(now - 100)
        e['HTTP_IF_MODIFIED_SINCE'] = t_mod
        out = BytesIO()
        resp = HTTPResponse(stdout=out)
        req = HTTPRequest(sys.stdin, e, resp)
        data = self.file.index_html(req, resp)
        self.assertEqual(resp.getStatus(), 200)
        self.assertEqual(data, str(self.file.data))

    def testIndexHtmlWithPdata(self):
        self.file.manage_upload('a' * (2 << 16))  # 128K
        self.file.index_html(self.app.REQUEST, self.app.REQUEST.RESPONSE)
        self.assertTrue(self.app.REQUEST.RESPONSE._wrote)

    def testIndexHtmlWithString(self):
        self.file.manage_upload('a' * 100)  # 100 bytes
        self.file.index_html(self.app.REQUEST, self.app.REQUEST.RESPONSE)
        self.assertTrue(not self.app.REQUEST.RESPONSE._wrote)

    def testStr(self):
        self.assertEqual(str(self.file), self.data)

    def testPrincipiaSearchSource_not_text(self):
        self.file.manage_edit('foobar', 'application/octet-stream',
                              filedata=''.join([chr(x) for x in range(256)]))
        self.assertEqual(self.file.PrincipiaSearchSource(), '')

    def testPrincipiaSearchSource_text(self):
        self.file.manage_edit('foobar', 'text/plain',
                              filedata='Now is the time for all good men to '
                                       'come to the aid of the Party.')
        self.assertTrue('Party' in self.file.PrincipiaSearchSource())

    def test_interfaces(self):
        from zope.interface.verify import verifyClass
        from OFS.Image import File
        from OFS.interfaces import IWriteLock
        from ZPublisher.HTTPRangeSupport import HTTPRangeInterface

        verifyClass(HTTPRangeInterface, File)
        verifyClass(IWriteLock, File)

    def testUnicode(self):
        val = u'some unicode string here'

        self.assertRaises(TypeError, self.file.manage_edit,
                          'foobar', 'text/plain', filedata=val)


class ImageTests(FileTests):
    data = open(filedata, 'rb').read()
    content_type = 'image/gif'
    factory = 'manage_addImage'

    def testUpdateData(self):
        self.file.update_data(self.data)
        self.assertEqual(self.file.size, len(self.data))
        self.assertEqual(self.file.data, self.data)
        self.assertEqual(self.file.width, 16)
        self.assertEqual(self.file.height, 16)

    def testStr(self):
        self.assertEqual(
            str(self.file),
            ('<img src="http://nohost/file" '
             'alt="" title="" height="16" width="16" />'))

    def testTag(self):
        tag_fmt = ('<img src="http://nohost/file" '
                   'alt="%s" title="%s" height="16" width="16" />')
        self.assertEqual(self.file.tag(), (tag_fmt % ('', '')))
        self.file.manage_changeProperties(title='foo')
        self.assertEqual(self.file.tag(), (tag_fmt % ('', 'foo')))
        self.file.manage_changeProperties(alt='bar')
        self.assertEqual(self.file.tag(), (tag_fmt % ('bar', 'foo')))

    def testViewImageOrFile(self):
        request = self.app.REQUEST
        response = request.RESPONSE
        result = self.file.index_html(request, response)
        self.assertEqual(result, self.data)

    def test_interfaces(self):
        from zope.interface.verify import verifyClass
        from OFS.Image import Image
        from OFS.interfaces import IWriteLock

        verifyClass(IWriteLock, Image)
