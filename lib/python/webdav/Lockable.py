##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

__version__ = "$Revision: 1.6 $"[11:-2]

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
    security.declareProtected('WebDAV Unlock items', 'wl_delLock')
    security.declareProtected('Manage WebDAV Locks', 'wl_clearLocks')

    # Setting default roles for permissions - we want owners of conent
    # to be able to lock.
    security.setPermissionDefault('WebDAV Lock items', ('Manager', 'Owner',))
    security.setPermissionDefault('WebDAV Unlock items',('Manager','Owner',))


    def wl_lockmapping(self, killinvalids=0, create=0):
        """ if 'killinvalids' is 1, locks who are no longer valid
        will be deleted """

        try: locks = getattr(self, '_dav_writelocks', None)
        except: locks = None

        if locks is None:
            if create:
                locks = self._dav_writelocks = PersistentMapping()
            else:
                # Don't generate a side effect transaction.
                locks = {}
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
        locks = self.wl_lockmapping(create=1)
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
        try:
            locks = self.wl_lockmapping()
            locks.clear()
        except:
            # The locks may be totally messed up, so we'll just delete
            # and replace.
            if hasattr(self, '_dav_writelocks'): del self._dav_writelocks
            if WriteLockInterface.isImplementedBy(self):
                self._dav_writelocks = PersistentMapping()

        # Call into a special hook used by LockNullResources to delete
        # themselves.  Could be used by other objects who want to deal
        # with the state of empty locks.
        if hasattr(Acquisition.aq_base(self), '__no_valid_write_locks__'):
            self.__no_valid_write_locks__()
    

import Globals
Globals.default__class_init__(LockableItem)


### Utility functions

def wl_isLocked(ob):
    """ Returns true if the object is locked, returns 0 if the object
    is not locked or does not implement the WriteLockInterface """
    return WriteLockInterface.isImplementedBy(ob) and ob.wl_isLocked()
