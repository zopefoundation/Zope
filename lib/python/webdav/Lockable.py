from WriteLockInterface import WriteLockInterface, LockItemInterface
from EtagSupport import EtagSupport
from LockItem import LockItem
from AccessControl import ClassSecurityInfo
from Globals import PersistentMapping
import Acquisition

class ResourceLockedError(Exception): pass

class LockableItem(EtagSupport):
    """\
    Implements the WriteLockInterface, and is inherited by Resource which
    is then inherited by the majority of Zope objects.  For an object to
    be lockable, however, it should have the WriteLockInterface in its
    __implements__ list, ie:

    __implements__ = (WriteLockInterface,)
    """

    # Protect methods using declarative security
    security = ClassSecurityInfo()
    security.declarePrivate('wl_lockmapping')
    security.declarePublic('wl_isLocked', 'wl_getLock', 'wl_isLockedByUser',
                           'wl_lockItems', 'wl_lockValues', 'wl_lockTokens',)
    security.declareProtected('WebDAV Lock items',
                              'wl_grantLockToUser', 'wl_setLock')
    security.declareProtected('WebDAV Unlock items',
                              'wl_delLock')
    security.declareProtected('Manage WebDAV Locks', 'wl_killAllLocks')


    def wl_lockmapping(self, killinvalids=0):
        """ if 'killinvalids' is 1, locks who are no longer valid
        will be deleted """

        try: locks = getattr(self, '_dav_writelocks', None)
        except: locks = None

        if locks is None:
            locks = self._dav_writelocks = PersistentMapping()
            return locks
        elif killinvalids:
            # Delete invalid locks
            for token, lock in locks.items():
                if not lock.isValid():
                    del locks[token]
            if (not locks) and hasattr(Acquisition.aq_base(self),
                                       '__no_valid_write_locks__'):
                self.__no_valid_write_locks__()
            return locks
        else:
            return locks

    def wl_lockItems(self, killinvalids=0):
        return self.wl_lockmapping(killinvalids).items()

    def wl_lockValues(self, killinvalids=0):
        return self.wl_lockmapping(killinvalids).values()

    def wl_lockTokens(self, killinvalids=0):
        return self.wl_lockmapping(killinvalids).keys()

    def wl_hasLock(self, token, killinvalids=0):
        if not token: return 0
        return token in self.wl_lockmapping(killinvalids).keys()

    def wl_isLocked(self):
        # returns true if 'self' is locked at all
        # We set 'killinvalids' to 1 to delete all locks who are no longer
        # valid (timeout has been exceeded)
        locks = self.wl_lockmapping(killinvalids=1)

        if locks.keys(): return 1
        else: return 0

    def wl_setLock(self, locktoken, lock):
        locks = self.wl_lockmapping()
        if LockItemInterface.isImplementedBy(lock):
            if locktoken == lock.getLockToken():
                locks[locktoken] = lock
            else:
                raise ValueError, 'Lock tokens do not match'
        else:
            raise ValueError, 'Lock does not implement the LockItem Interface'

    def wl_getLock(self, locktoken):
        locks = self.wl_lockmapping(killinvalids=1)
        return locks.get(locktoken, None)

    def wl_delLock(self, locktoken):
        locks = self.wl_lockmapping()
        if locks.has_key(locktoken):
            del locks[locktoken]

    def wl_clearLocks(self):
        # Called by lock management machinery to quickly and effectively
        # destroy all locks.
        locks = self.wl_lockmapping()
        locks.clear()
        if hasattr(Acquisition.aq_base(self), '__no_valid_write_locks__'):
            self.__no_valid_write_locks__()
    

import Globals
Globals.default__class_init__(LockableItem)


### Utility functions

def wl_isLocked(ob):
    """ Returns true if the object is locked, returns 0 if the object
    is not locked or does not implement the WriteLockInterface """
    return WriteLockInterface.isImplementedBy(ob) and ob.wl_isLocked()
