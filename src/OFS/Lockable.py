##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import webdav_lock_items
from AccessControl.Permissions import webdav_manage_locks
from AccessControl.Permissions import webdav_unlock_items
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from OFS.EtagSupport import EtagSupport
from OFS.interfaces import ILockItem
from OFS.interfaces import IWriteLock
from Persistence import PersistentMapping
from zope.interface import implementer


@implementer(IWriteLock)
class LockableItem(EtagSupport):
    """Implements the WriteLock interface.
    """

    # Protect methods using declarative security
    security = ClassSecurityInfo()

    # Setting default roles for permissions - we want owners of conent
    # to be able to lock.
    security.setPermissionDefault(webdav_lock_items, ('Manager', 'Owner',))
    security.setPermissionDefault(webdav_unlock_items, ('Manager', 'Owner',))

    @security.private
    def wl_lockmapping(self, killinvalids=0, create=0):
        """ if 'killinvalids' is 1, locks who are no longer valid
        will be deleted """

        try:
            locks = getattr(self, '_dav_writelocks', None)
        except Exception:
            locks = None

        if locks is None:
            if create:
                locks = self._dav_writelocks = PersistentMapping()
            else:
                # Don't generate a side effect transaction.
                locks = {}
            return locks
        elif killinvalids:
            # Delete invalid locks
            for token, lock in list(locks.items()):
                if not lock.isValid():
                    del locks[token]
            if (not locks) and hasattr(aq_base(self),
                                       '__no_valid_write_locks__'):
                self.__no_valid_write_locks__()
            return locks
        else:
            return locks

    @security.public
    def wl_lockItems(self, killinvalids=0):
        return list(self.wl_lockmapping(killinvalids).items())

    @security.public
    def wl_lockValues(self, killinvalids=0):
        return list(self.wl_lockmapping(killinvalids).values())

    @security.public
    def wl_lockTokens(self, killinvalids=0):
        return list(self.wl_lockmapping(killinvalids).keys())

    # TODO: Security Declaration
    def wl_hasLock(self, token, killinvalids=0):
        if not token:
            return 0
        return token in list(self.wl_lockmapping(killinvalids).keys())

    @security.public
    def wl_isLocked(self):
        # returns true if 'self' is locked at all
        # We set 'killinvalids' to 1 to delete all locks who are no longer
        # valid (timeout has been exceeded)
        locks = self.wl_lockmapping(killinvalids=1)

        if list(locks.keys()):
            return 1
        else:
            return 0

    @security.protected(webdav_lock_items)
    def wl_setLock(self, locktoken, lock):
        locks = self.wl_lockmapping(create=1)
        if ILockItem.providedBy(lock):
            if locktoken == lock.getLockToken():
                locks[locktoken] = lock
            else:
                raise ValueError('Lock tokens do not match')
        else:
            raise ValueError('Lock does not implement the LockItem Interface')

    @security.public
    def wl_getLock(self, locktoken):
        locks = self.wl_lockmapping(killinvalids=1)
        return locks.get(locktoken, None)

    @security.protected(webdav_unlock_items)
    def wl_delLock(self, locktoken):
        locks = self.wl_lockmapping()
        if locktoken in locks:
            del locks[locktoken]

    @security.protected(webdav_manage_locks)
    def wl_clearLocks(self):
        # Called by lock management machinery to quickly and effectively
        # destroy all locks.
        try:
            locks = self.wl_lockmapping()
            locks.clear()
        except Exception:
            # The locks may be totally messed up, so we'll just delete
            # and replace.
            if hasattr(self, '_dav_writelocks'):
                del self._dav_writelocks
            if IWriteLock.providedBy(self):
                self._dav_writelocks = PersistentMapping()

        # Call into a special hook used by LockNullResources to delete
        # themselves.  Could be used by other objects who want to deal
        # with the state of empty locks.
        if hasattr(aq_base(self), '__no_valid_write_locks__'):
            self.__no_valid_write_locks__()


InitializeClass(LockableItem)


def wl_isLocked(ob):
    """ Returns true if the object is locked, returns 0 if the object
    is not locked or does not implement the WriteLockInterface """
    return wl_isLockable(ob) and ob.wl_isLocked()


def wl_isLockable(ob):
    return IWriteLock.providedBy(ob)
