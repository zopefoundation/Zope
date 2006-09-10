import unittest
import Testing
import Zope2
Zope2.startup()

from Testing.makerequest import makerequest
import transaction
import base64

auth_info = 'Basic %s' % base64.encodestring('manager:secret').rstrip()


class TestPUTFactory(unittest.TestCase):

    def setUp(self):
        self.app = makerequest(Zope2.app())
        try:
            # Make a manager user
            uf = self.app.acl_users
            uf._doAddUser('manager', 'secret', ['Manager'], [])
            # Make a folder to put stuff into
            self.app.manage_addFolder('folder', '')
            self.folder = self.app.folder
            # Fake a WebDAV PUT request
            request = self.app.REQUEST
            request['PARENTS'] = [self.app]
            request['BODY'] = 'bar'
            request.environ['CONTENT_TYPE'] = 'text/plain'
            request.environ['REQUEST_METHOD'] = 'PUT'
            request._auth = auth_info
        except:
            self.tearDown()
            raise

    def tearDown(self):
        transaction.abort()
        self.app.REQUEST.close()
        self.app._p_jar.close()

    def testNoVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/folder/doc')
        put(request, request.RESPONSE)
        self.failUnless('doc' in self.folder.objectIds())

    def testSimpleVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/VirtualHostRoot/folder/doc')
        put(request, request.RESPONSE)
        self.failUnless('doc' in self.folder.objectIds())

    def testSubfolderVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/folder/VirtualHostRoot/doc')
        put(request, request.RESPONSE)
        self.failUnless('doc' in self.folder.objectIds())

    def testInsideOutVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/VirtualHostRoot/_vh_foo/folder/doc')
        put(request, request.RESPONSE)
        self.failUnless('doc' in self.folder.objectIds())

    def testSubfolderInsideOutVirtualHosting(self):
        request = self.app.REQUEST
        put = request.traverse('/VirtualHostBase/http/foo.com:80/folder/VirtualHostRoot/_vh_foo/doc')
        put(request, request.RESPONSE)
        self.failUnless('doc' in self.folder.objectIds())


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestPUTFactory),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
