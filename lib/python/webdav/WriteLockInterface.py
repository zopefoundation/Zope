##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

__version__='$Revision: 1.4 $'[11:-2]

import Interface

class LockItemInterface(Interface.Base):
    """\
    A LockItem contains information about a lock.  This includes:

     o The locktoken uri (used to identify the lock by WebDAV)

     o The lock owner (The string passed in the 'owner' property by WebDAV)

     o The lock creator (the Zope user who physically owns the lock)

     o Depth

     o Timeout information

     o Modified time (for calculating timeouts)

     o LockType (only EXCLUSIVE is supported right now)

    """

    def __init__(self, creator, owner, depth=0, timeout='Infinity',
                 locktype='write', lockscope='exclusive', token=None):
        """\
        If any of the  following are untrue, a **ValueError** exception
        will be raised.

         - **creator** MUST be a Zope user object or string to find a
           valid user object.

         - **owner** MUST be a nonempty string, or type that can be converted
           to a nonempty string.

         - **depth** MUST be in the set {0,'infinity'}

         - **timeout** MUST either be an integer, or a string in the form
           of 'Seconds-nnn' where nnn is an integer.  The timeout value
           MUST be less than (2^32)-1.  *IF* timeout is the string value
           'Infinite', the timeout value will be set to 1800 (30 minutes).
           (Timeout is the value in seconds from creation\modification
           time until the lock MAY time out).

         - **locktype** not in set {'write'} *this may expand later*

         - **lockscope** not in set {'exclusive'} *this may expand later*

        If the value passed in to 'token' is 'None', the a new locktoken
        will be generated during the construction process.

        __init__ must generate the opaquelocktoken uri used to identify the
        lock (if 'token' is 'None')and set all of the above attributes on
        the object.
        """

    def getCreator(self):
        """ Returns the Zope user who created the lock.  This is returned
        in a tuple containing the Users ID and the path to the user folder
        they came from."""

    def getCreatorPath(self):
        """ Returns a string of the path to the user object in the user
        folder they were found in. """

    def getOwner(self):
        """ Returns the string value of the 'owner' property sent
        in by WebDAV """

    def getLockToken(self):
        """ returns the opaque lock token """

    def getDepth(self):
        """ returns the depth of the lock """

    def getTimeout(self):
        """ returns an integer value of the timeout setting """

    def getTimeoutString(self):
        """ returns the timeout value in a form acceptable by
        WebDAV (ie - 'Seconds-40800') """

    def setTimeout(self, newtimeout):
        """ refreshes the timeout information """

    def getModifiedTime(self):
        """ returns a time.time value of the last time the Lock was
        modified.  From RFC 2518:

         The timeout counter SHOULD be restarted any time an owner of the
         lock sends a method to any member of the lock, including unsupported
         methods or methods which are unsucscessful.   The lock MUST be
         refreshed if a refresh LOCK method is successfully received.

        The modified time is used to calculate the refreshed value """

    def refresh(self):
        """ Tickles the locks modified time by setting it to the current
        time.time() value.  (As stated in the RFC, the timeout counter
        SHOULD be restarted for any HTTP method called by the lock owner
        on the locked object). """

    def isValid(self):
        """ Returns true if (self.getModifiedTime() + self.getTimeout())
        is greater than the current time.time() value. """
        # now = time.time()
        # modified = self.getModifiedTime()
        # timeout = self.getTimeout()
        #
        # return (modified + timeout > now)    # there's time remaining

    def getLockType(self):
        """ returns the lock type ('write') """

    def getLockScope(self):
        """ returns the lock scope ('exclusive') """

    def asLockDiscoveryProperty(self, ns='d'):
        """ Return the lock rendered as an XML representation of a
        WebDAV 'lockdiscovery' property.  'ns' is the namespace identifier
        used on the XML elements."""

    def asXML(self):
        """ Render a full XML representation of a lock for WebDAV,
        used when returning the value of a newly created lock. """
        
class WriteLockInterface(Interface.Base):
    """\
    This represents the basic protocol needed to support the write lock
    machinery.

    It must be able to answer the questions:

     o Is the object locked?

     o Is the lock owned by the current user?

     o What lock tokens are associated with the current object?

     o What is their state (how long until they're supposed to time out?,
       what is their depth?  what type are they?

    And it must be able to do the following:

     o Grant a write lock on the object to a specified user.

       - *If lock depth is infinite, this must also grant locks on **all**
         subobjects, or fail altogether*

     o Revoke a lock on the object.

       - *If lock depth is infinite, this must also revoke locks on all
         subobjects*

    **All methods in the WriteLock interface that deal with checking valid
    locks MUST check the timeout values on the lockitem (ie, by calling
    'lockitem.isValid()'), and DELETE the lock if it is no longer valid**

    """

    
    def wl_lockItems(self, killinvalids=0):
        """ Returns (key, value) pairs of locktoken, lock.

        if 'killinvalids' is true, invalid locks (locks whose timeout
        has been exceeded) will be deleted"""

    def wl_lockValues(self, killinvalids=0):
        """ Returns a sequence of locks.  if 'killinvalids' is true,
        invalid locks will be deleted"""

    def wl_lockTokens(self, killinvalids=0):
        """ Returns a sequence of lock tokens.  if 'killinvalids' is true,
        invalid locks will be deleted"""

    def wl_hasLock(self, token, killinvalids=0):
        """ Returns true if the lock identified by the token is attached
        to the object. """

    def wl_isLocked(self):
        """ Returns true if 'self' is locked at all.  If invalid locks
        still exist, they should be deleted."""

    def wl_setLock(self, locktoken, lock):
        """ Store the LockItem, 'lock'.  The locktoken will be used to fetch
        and delete the lock.  If the lock exists, this MUST
        overwrite it if all of the values except for the 'timeout' on the
        old and new lock are the same. """

    def wl_getLock(self, locktoken):
        """ Returns the locktoken identified by the locktokenuri """

    def wl_delLock(self, locktoken):
        """ Deletes the locktoken identified by the locktokenuri """
        
    def wl_clearLocks(self):
        """ Deletes ALL DAV locks on the object - should only be called
        by lock management machinery. """
        
