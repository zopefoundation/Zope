import unittest

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.SecurityManager import setSecurityPolicy
from OFS.interfaces import IWriteLock
from zExceptions import Forbidden
from zope.interface import implementer


class _DummySecurityPolicy:

    def checkPermission(self, permission, object, context):
        return False


@implementer(IWriteLock)
class _DummyContent:

    def __init__(self, token=None):
        self.token = token

    def wl_hasLock(self, token):
        return self.token == token

    def wl_isLocked(self):
        return bool(self.token)


class TestUnlock(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.davcmds import Unlock

        return Unlock

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_apply_bogus_lock(self):
        """
        When attempting to unlock a resource with a token that the
        resource hasn't been locked with, we should return an error
        instead of a 20X response.  See
        http://lists.w3.org/Archives/Public/w3c-dist-auth/2001JanMar/0099.html
        for rationale.

        Prior to Zope 2.11, we returned a 204 under this circumstance.
        We choose do what mod_dav does, which is return a '400 Bad
        Request' error.

        This was caught by litmus locks.notowner_lock test #10.
        """
        inst = self._makeOne()
        lockable = _DummyContent()
        result = inst.apply(lockable, 'bogus',
                            url='http://example.com/foo/UNLOCK', top=0)
        result = result.getvalue()
        self.assertNotEqual(
            result.find('<d:status>HTTP/1.1 400 Bad Request</d:status>'),
            -1)


class TestPropPatch(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.davcmds import PropPatch

        return PropPatch

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_parse_xml_property_values_with_namespaces(self):
        """
        Before Zope 2.11, litmus props tests 19: propvalnspace and 20:
        propwformed were failing because Zope did not strip off the
        xmlns: attribute attached to XML property values.  We now strip
        off all attributes that look like xmlns declarations.
        """

        reqbody = """<?xml version="1.0" encoding="utf-8" ?>
                     <propertyupdate xmlns='DAV:'>
                     <set>
                     <prop>
                     <t:valnspace xmlns:t='http://webdav.org/neon/litmus/'>
                     <foo xmlns='bar'/>
                     </t:valnspace>
                     </prop>
                     </set>
                     </propertyupdate>"""

        request = {'BODY': reqbody}

        inst = self._makeOne(request)
        self.assertEqual(len(inst.values), 1)
        self.assertEqual(inst.values[0][3]['__xml_attrs__'], {})


class TestDeleteCollection(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.davcmds import DeleteCollection

        return DeleteCollection

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def setUp(self):
        self._oldPolicy = setSecurityPolicy(_DummySecurityPolicy())

    def tearDown(self):
        noSecurityManager()
        setSecurityPolicy(self._oldPolicy)

    def test_apply_no_parent(self):
        cmd = self._makeOne()
        obj = _DummyContent()
        sm = getSecurityManager()
        self.assertEqual(cmd.apply(obj, None, sm, '/foo/DELETE'), '')

    def test_apply_no_col_Forbidden(self):
        cmd = self._makeOne()
        obj = _DummyContent()
        obj.__parent__ = _DummyContent()
        sm = getSecurityManager()
        self.assertRaises(Forbidden, cmd.apply, obj, None, sm, '/foo/DELETE')

    def test_apply_no_col_Locked(self):
        from webdav.common import Locked

        cmd = self._makeOne()
        obj = _DummyContent('LOCKED')
        sm = getSecurityManager()
        self.assertRaises(Locked, cmd.apply, obj, None, sm, '/foo/DELETE')
