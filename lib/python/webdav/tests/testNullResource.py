import unittest


class TestLockNullResource(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.interfaces import IWriteLock
        from webdav.NullResource import LockNullResource
        from zope.interface.verify import verifyClass

        verifyClass(IWriteLock, LockNullResource)


class TestNullResource(unittest.TestCase):

    def _getTargetClass(self):
        from webdav.NullResource import NullResource
        return NullResource

    def _makeOne(self, parent=None, name='nonesuch', **kw):
        return self._getTargetClass()(parent, name, **kw)

    def test_z3interfaces(self):
        from webdav.interfaces import IWriteLock
        from zope.interface.verify import verifyClass

        verifyClass(IWriteLock, self._getTargetClass())

    def test_HEAD_locks_empty_body_before_raising_NotFound(self):
        from zExceptions import NotFound
        # See https://bugs.launchpad.net/bugs/239636
        class DummyResponse:
            _server_version = 'Dummy' # emulate ZServer response
            locked = False
            body = None
            def setHeader(self, *args):
                pass
            def setBody(self, body, lock=False):
                self.body = body
                self.locked = bool(lock)

        nonesuch = self._makeOne()
        request = {}
        response = DummyResponse()

        self.assertRaises(NotFound, nonesuch.HEAD, request, response)

        self.assertEqual(response.body, '')
        self.failUnless(response.locked)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestLockNullResource),
        unittest.makeSuite(TestNullResource),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
