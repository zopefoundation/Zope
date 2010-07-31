import unittest
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from Acquisition import Implicit


MS_DAV_AGENT = "Microsoft Data Access Internet Publishing Provider DAV"

def make_request_response(environ=None):
    from StringIO import StringIO
    from ZPublisher.HTTPRequest import HTTPRequest
    from ZPublisher.HTTPResponse import HTTPResponse
    
    if environ is None:
        environ = {}

    stdout = StringIO()
    stdin = StringIO()
    resp = HTTPResponse(stdout=stdout)
    environ.setdefault('SERVER_NAME', 'foo')
    environ.setdefault('SERVER_PORT', '80')
    environ.setdefault('REQUEST_METHOD', 'GET')
    req = HTTPRequest(stdin, environ, resp)
    return req, resp

class TestResource(unittest.TestCase):
    def setUp(self):
        self.app = DummyContent()
        self.app.acl_users = DummyUserFolder()
        self._policy = PermissiveSecurityPolicy()
        self._oldPolicy = setSecurityPolicy(self._policy)
        newSecurityManager(None, OmnipotentUser().__of__(self.app.acl_users))

    def tearDown(self):
        noSecurityManager()
        setSecurityPolicy(self._oldPolicy)

    def _getTargetClass(self):
        from webdav.Resource import Resource
        return Resource

    def _makeOne(self):
        klass = self._getTargetClass()
        inst = klass()
        return inst

    def test_interfaces(self):
        from webdav.interfaces import IDAVResource
        from webdav.interfaces import IWriteLock
        Resource = self._getTargetClass()
        from zope.interface.verify import verifyClass

        verifyClass(IDAVResource, Resource)
        verifyClass(IWriteLock, Resource)

    def test_ms_author_via(self):
        import webdav
        from webdav.Resource import Resource

        default_settings = webdav.enable_ms_author_via
        try:
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('ms-author-via'))

            webdav.enable_ms_author_via = True
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('ms-author-via'))

            req, resp = make_request_response(
                environ={'USER_AGENT': MS_DAV_AGENT})
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(resp.headers.has_key('ms-author-via'))
            self.assert_(resp.headers['ms-author-via'] == 'DAV')

        finally:
            webdav.enable_ms_author_via = default_settings

    def test_ms_public_header(self):
        import webdav
        from webdav.Resource import Resource
        default_settings = webdav.enable_ms_public_header
        try:
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('public'))

            webdav.enable_ms_public_header = True
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('public'))
            self.assert_(resp.headers.has_key('allow'))

            req, resp = make_request_response(
                environ={'USER_AGENT': MS_DAV_AGENT})
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(resp.headers.has_key('public'))
            self.assert_(resp.headers.has_key('allow'))
            self.assert_(resp.headers['public'] == resp.headers['allow'])

        finally:
            webdav.enable_ms_public_header = default_settings

    def test_MOVE_self_locked(self):
        """
        DAV: litmus"notowner_modify" tests warn during a MOVE request
        because we returned "412 Precondition Failed" instead of "423
        Locked" when the resource attempting to be moved was itself
        locked.  Fixed by changing Resource.Resource.MOVE to raise the
        correct error.
        """
        app = self.app
        request = DummyRequest({}, {})
        response = DummyResponse()
        inst = self._makeOne()
        inst.cb_isMoveable = lambda *arg: True
        inst.restrictedTraverse = lambda *arg: app
        inst.getId = lambda *arg: '123'
        inst._dav_writelocks = {'a':DummyLock()}
        from zope.interface import directlyProvides
        from webdav.interfaces import IWriteLock
        directlyProvides(inst, IWriteLock)
        from webdav.common import Locked
        self.assertRaises(Locked, inst.MOVE, request, response)

    def dont_test_dav__simpleifhandler_fail_cond_put_unlocked(self):
        """
        DAV: litmus' cond_put_unlocked test (#22) exposed a bug in
        webdav.Resource.dav__simpleifhandler.  If the resource is not
        locked, and a DAV request contains an If header, no token can
        possibly match and we must return a 412 Precondition Failed
        instead of 204 No Content.

        I (chrism) haven't been able to make this work properly
        without breaking other litmus tests (32. lock_collection being
        the most important), so this test is not currently running.
        """
        ifhdr = 'If: (<locktoken:foo>)'
        request = DummyRequest({'URL':'http://example.com/foo/PUT'},
                               {'If':ifhdr})
        response = DummyResponse()
        inst = self._makeOne()
        from zope.interface import directlyProvides
        from webdav.interfaces import IWriteLock
        directlyProvides(inst, IWriteLock)
        from webdav.common import PreconditionFailed
        self.assertRaises(PreconditionFailed, inst.dav__simpleifhandler,
                          request, response)

    def dont_test_dav__simpleifhandler_cond_put_corrupt_token(self):
        """
        DAV: litmus' cond_put_corrupt_token test (#18) exposed a bug
        in webdav.Resource.dav__simpleifhandler.  If the resource is
        locked at all, and a DAV request contains an If header, and
        none of the lock tokens present in the header match a lock on
        the resource, we need to return a 423 Locked instead of 204 No
        Content.

        I (chrism) haven't been able to make this work properly
        without breaking other litmus tests (32. lock_collection being
        the most important), so this test is not currently running.
        """
        ifhdr = 'If: (<locktoken:foo>) (Not <DAV:no-lock>)'
        request = DummyRequest({'URL':'http://example.com/foo/PUT'},
                               {'If':ifhdr})
        response = DummyResponse()
        inst = self._makeOne()
        inst._dav_writelocks = {'a':DummyLock()}
        from zope.interface import directlyProvides
        from webdav.interfaces import IWriteLock
        directlyProvides(inst, IWriteLock)
        from webdav.common import Locked
        self.assertRaises(Locked, inst.dav__simpleifhandler, request, response)

class DummyLock:
    def isValid(self):
        return True

class DummyContent(Implicit):
    def cb_isMoveable(self):
        return True

    def _checkId(self, *arg, **kw):
        return True

    def _verifyObjectPaste(self, *arg):
        return True

class DummyUserFolder(Implicit):
    pass

class DummyRequest:
    def __init__(self, form, headers):
        self.form = form
        self.headers = headers
        
    def get_header(self, name, default):
        return self.headers.get(name, default)

    def get(self, name, default):
        return self.form.get(name, default)

    def __getitem__(self, name):
        return self.form[name]

    def physicalPathFromURL(self, *arg):
        return ['']

class DummyResponse:
    def __init__(self):
        self.headers = {}

    def setHeader(self, name, value, *arg):
        self.headers[name] = value

from AccessControl.PermissionRole import rolesForPermissionOn
from Acquisition import Implicit


class PermissiveSecurityPolicy:
    """
        Very permissive security policy for unit testing purposes.
    """
    #
    #   Standard SecurityPolicy interface
    #
    def validate( self
                , accessed=None
                , container=None
                , name=None
                , value=None
                , context=None
                , roles=None
                , *args
                , **kw):
        if name and name.startswith('hidden'):
            return False
        else:
            return True

    def checkPermission(self, permission, object, context):
        if permission == 'forbidden permission':
            return 0
        if permission == 'addFoo':
            return context.user.allowed(object, ['FooAdder'])
        roles = rolesForPermissionOn(permission, object)
        if isinstance(roles, basestring):
            roles=[roles]
        return context.user.allowed(object, roles)


class OmnipotentUser( Implicit ):
    """
      Omnipotent User for unit testing purposes.
    """
    def getId( self ):
        return 'all_powerful_Oz'

    getUserName = getId

    def getRoles(self):
        return ('Manager',)

    def allowed( self, object, object_roles=None ):
        return 1

    def getRolesInContext(self, object):
        return ('Manager',)

    def _check_context(self, object):
        return True

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestResource),
        ))
