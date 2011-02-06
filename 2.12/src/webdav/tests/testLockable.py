import unittest

class TestUtilFunctions(unittest.TestCase):
    def test_wl_isLocked(self):
        from webdav.Lockable import wl_isLocked
        unlockable = UnlockableResource()
        self.failIf(wl_isLocked(unlockable))
        lockable_unlocked = LockableResource(locked=False)
        self.failIf(wl_isLocked(lockable_unlocked))
        lockable_locked = LockableResource(locked=True)
        self.failUnless(wl_isLocked(lockable_locked))

    def test_wl_isLockable(self):
        from webdav.Lockable import wl_isLockable
        unlockable = UnlockableResource()
        self.failIf(wl_isLockable(unlockable))
        lockable = LockableResource(locked=False)
        self.failUnless(wl_isLockable(lockable))

from webdav.interfaces import IWriteLock
from zope.interface import implements

class LockableResource:
    implements(IWriteLock)
    def __init__(self, locked):
        self.locked = locked
    def wl_isLocked(self):
        return self.locked

class UnlockableResource:
    pass

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestUtilFunctions),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
