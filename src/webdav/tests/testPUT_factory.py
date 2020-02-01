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
