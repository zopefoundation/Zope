import base64
import unittest

import transaction
import Zope2
from Products.SiteAccess.VirtualHostMonster import VirtualHostMonster
from Testing.makerequest import makerequest


auth_info = b'Basic %s' % base64.encodebytes(b'manager:secret').rstrip()

Zope2.startup_wsgi()


class TestPUTFactory(unittest.TestCase):

    def setUp(self):
        self.app = makerequest(Zope2.app())
        # Make a manager user
        uf = self.app.acl_users
        uf._doAddUser('manager', 'secret', ['Manager'], [])
        # Make a folder to put stuff into
        self.app.manage_addFolder('folder', '')
        self.folder = self.app.folder
        # Setup VHM
        if 'virtual_hosting' not in self.app:
            vhm = VirtualHostMonster()
            vhm.addToContainer(self.app)
        # Fake a WebDAV PUT request
        request = self.app.REQUEST
        request['PARENTS'] = [self.app]
        request['BODY'] = 'bar'
        request['BODYFILE'] = b'bar'
        request.environ['CONTENT_TYPE'] = 'text/plain'
        request.environ['REQUEST_METHOD'] = 'PUT'
        request.environ['WEBDAV_SOURCE_PORT'] = 1
        request._auth = auth_info

    def tearDown(self):
        transaction.abort()
        self.app.REQUEST.close()
        self.app._p_jar.close()

    def testNoVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/folder/doc')
        put(request, request.RESPONSE)
        self.assertTrue('doc' in self.folder.objectIds())

    def testSimpleVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/'
                               'VirtualHostRoot/folder/doc')
        put(request, request.RESPONSE)
        self.assertTrue('doc' in self.folder.objectIds())

    def testSubfolderVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/'
                               'folder/VirtualHostRoot/doc')
        put(request, request.RESPONSE)
        self.assertTrue('doc' in self.folder.objectIds())

    def testInsideOutVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/'
                               'VirtualHostRoot/_vh_foo/folder/doc')
        put(request, request.RESPONSE)
        self.assertTrue('doc' in self.folder.objectIds())

    def testSubfolderInsideOutVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/'
                               'folder/VirtualHostRoot/_vh_foo/doc')
        put(request, request.RESPONSE)
        self.assertTrue('doc' in self.folder.objectIds())

    def testCollector2261(self):
        from OFS.DTMLMethod import addDTMLMethod

        self.app.manage_addFolder('A', '')
        addDTMLMethod(self.app, 'a', file='I am file a')
        self.app.A.manage_addFolder('B', '')
        request = self.app.REQUEST
        # this should create 'a' within /A/B containing 'bar'
        put = request.traverse('/A/B/a')
        put(request, request.RESPONSE)
        # PUT should no acquire A.a
        self.assertEqual(str(self.app.A.a), 'I am file a',
                         'PUT factory should not acquire content')
        # check for the newly created file
        self.assertEqual(str(self.app.A.B.a), 'bar')

    def testPUT_factory_changes_name(self):
        # A custom PUT factory may want to change the object ID,
        # for example to remove file name extensions.
        from OFS.Image import File

        def custom_put_factory(name, typ, body):
            new_name = 'newname'
            if not isinstance(body, bytes):
                body = body.encode('UTF-8')
            return File(new_name, '', body, content_type=typ)
        self.app.folder.PUT_factory = custom_put_factory

        request = self.app.REQUEST
        put = request.traverse('/folder/doc')
        put(request, request.RESPONSE)
        self.assertTrue('newname' in self.folder.objectIds())

    def test_default_PUT_factory_type_guessing(self):
        # Check how the default PUT factory guesses the type of object to
        # create. It is based on either the content-type request header or the
        # file name.
        from OFS.DTMLDocument import DTMLDocument
        from OFS.Image import File
        from OFS.Image import Image
        from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
        request = self.app.REQUEST

        # DTML documents
        put = request.traverse('/folder/doc.dtml')
        put(request, request.RESPONSE)
        self.assertIsInstance(self.folder['doc.dtml'], DTMLDocument)

        # Page Templates
        # PUT and content type guessing is messed up for ZopePageTemplates
        request.environ['CONTENT_TYPE'] = 'text/html'
        request['BODY'] = b'bar'
        put = request.traverse('/folder/zpt1')
        put(request, request.RESPONSE)
        self.assertIsInstance(self.folder.zpt1, ZopePageTemplate)
        self.assertEqual(self.folder.zpt1.content_type, 'text/html')

        request['BODY'] = b'<?xml version="1.0" encoding="UTF-8"?>bar'
        put = request.traverse('/folder/zpt2')
        put(request, request.RESPONSE)
        self.assertIsInstance(self.folder.zpt2, ZopePageTemplate)
        self.assertEqual(self.folder.zpt2.content_type, 'text/xml')

        for html_extension in ('.pt', '.zpt', '.html', '.htm'):
            ob_id = 'zpt%s' % html_extension
            request.environ['CONTENT_TYPE'] = 'application/octet-stream'
            request['BODY'] = b'<html></html>'
            put = request.traverse('/folder/%s' % ob_id)
            put(request, request.RESPONSE)
            zope_ob = getattr(self.folder, ob_id)
            self.assertIsInstance(zope_ob, ZopePageTemplate)
            self.assertEqual(zope_ob.content_type, 'text/html')

        request.environ['CONTENT_TYPE'] = 'application/octet-stream'
        put = request.traverse('/folder/zpt.xml')
        put(request, request.RESPONSE)
        zope_ob = self.folder['zpt.xml']
        self.assertIsInstance(zope_ob, ZopePageTemplate)
        self.assertEqual(zope_ob.content_type, 'text/xml')

        # Images
        for content_type in ('image/jpg', 'image/gif', 'image/png'):
            request.environ['CONTENT_TYPE'] = content_type
            ob_id = 'img_%s' % content_type.replace('/', '_')
            put = request.traverse('/folder/%s' % ob_id)
            put(request, request.RESPONSE)
            zope_ob = getattr(self.folder, ob_id)
            self.assertIsInstance(zope_ob, Image)
            self.assertEqual(zope_ob.content_type, content_type)

        for extension in ('.jpg', '.jpeg', '.gif', '.png', '.tiff'):
            ob_id = 'img%s' % extension
            request.environ['CONTENT_TYPE'] = 'application/octet-stream'
            put = request.traverse('/folder/%s' % ob_id)
            put(request, request.RESPONSE)
            zope_ob = getattr(self.folder, ob_id)
            self.assertIsInstance(zope_ob, Image)

        # File, the last fallback
        for content_type in ('text/plain', 'application/pdf',
                             'application/octet-stream'):
            request.environ['CONTENT_TYPE'] = content_type
            request['BODY'] = b'foobar'
            ob_id = 'file_%s' % content_type.replace('/', '_')
            put = request.traverse('/folder/%s' % ob_id)
            put(request, request.RESPONSE)
            zope_ob = getattr(self.folder, ob_id)
            self.assertIsInstance(zope_ob, File)
            self.assertEqual(zope_ob.content_type, content_type)
