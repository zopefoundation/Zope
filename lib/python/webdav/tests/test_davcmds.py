import unittest

class TestUnlock(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.davcmds import Unlock
        return Unlock

    def _makeOne(self):
        klass = self._getTargetClass()
        return klass()

    def _makeLockable(self, locktoken):
        from webdav.interfaces import IWriteLock
        from zope.interface import implements
        class Lockable:
            implements(IWriteLock)
            def __init__(self, token):
                self.token = token
            def wl_hasLock(self, token):
                return self.token == token
        return Lockable(locktoken)

    def test_apply_nontop_resource_returns_string(self):
        """ When top=0 in unlock constructor, prior to Zope 2.11, the
        unlock.apply method would return a StringIO.  This was bogus
        because a StringIO cannot be used as a response body via the
        standard RESPONSE.setBody() command.  Only strings or objects
        with an asHTML method may be passed into setBody()."""

        inst = self._makeOne()
        lockable = self._makeLockable(None)
        result = inst.apply(lockable, 'bogus',
                            url='http://example.com/foo/UNLOCK', top=0)
        self.failUnless(isinstance(result, str))

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
        lockable = self._makeLockable(None)
        result = inst.apply(lockable, 'bogus',
                            url='http://example.com/foo/UNLOCK', top=0)
        self.assertNotEqual(
            result.find('<d:status>HTTP/1.1 400 Bad Request</d:status>'),
            -1)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestUnlock),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')

