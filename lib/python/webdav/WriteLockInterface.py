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
"""Write lock interfaces.

$Id$
"""

from Interface import Interface


class LockItemInterface(Interface):

    """A LockItem contains information about a lock.

    This includes:

     o The locktoken uri (used to identify the lock by WebDAV)

     o The lock owner (The string passed in the 'owner' property by WebDAV)

     o The lock creator (the Zope user who physically owns the lock)

     o Depth

     o Timeout information

     o Modified time (for calculating timeouts)

     o LockType (only EXCLUSIVE is supported right now)

    """

    # XXX:  WAAAA!  What is a ctor doing in the interface?
    def __init__(creator, owner, depth=0, timeout='Infinity',
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

    def getCreator():
        """ Returns the Zope user who created the lock.  This is returned
        in a tuple containing the Users ID and the path to the user folder
        they came from."""

    def getCreatorPath():
        """ Returns a string of the path to the user object in the user
        folder they were found in. """

    def getOwner():
        """ Returns the string value of the 'owner' property sent
        in by WebDAV """

    def getLockToken():
        """ returns the opaque lock token """

    def getDepth():
        """ returns the depth of the lock """

    def getTimeout():
        """ returns an integer value of the timeout setting """

    def getTimeoutString():
        """ returns the timeout value in a form acceptable by
        WebDAV (ie - 'Seconds-40800') """

    def setTimeout(newtimeout):
        """ refreshes the timeout information """

    def getModifiedTime():
        """ returns a time.time value of the last time the Lock was
        modified.  From RFC 2518:

         The timeout counter SHOULD be restarted any time an owner of the
         lock sends a method to any member of the lock, including unsupported
         methods or methods which are unsucscessful.   The lock MUST be
         refreshed if a refresh LOCK method is successfully received.

        The modified time is used to calculate the refreshed value """

    def refresh():
        """ Tickles the locks modified time by setting it to the current
        time.time() value.  (As stated in the RFC, the timeout counter
        SHOULD be restarted for any HTTP method called by the lock owner
        on the locked object). """

    def isValid():
        """ Returns true if (self.getModifiedTime() + self.getTimeout())
        is greater than the current time.time() value. """
        # now = time.time()
        # modified = self.getModifiedTime()
        # timeout = self.getTimeout()
        #
        # return (modified + timeout > now)    # there's time remaining

    def getLockType():
        """ returns the lock type ('write') """

    def getLockScope():
        """ returns the lock scope ('exclusive') """

    def asLockDiscoveryProperty(ns='d'):
        """ Return the lock rendered as an XML representation of a
        WebDAV 'lockdiscovery' property.  'ns' is the namespace identifier
        used on the XML elements."""

    def asXML():
        """ Render a full XML representation of a lock for WebDAV,
        used when returning the value of a newly created lock. """


# create WriteLockInterface
from Interface.bridge import createZope3Bridge
from interfaces import IWriteLock
import WriteLockInterface

createZope3Bridge(IWriteLock, WriteLockInterface, 'WriteLockInterface')

del createZope3Bridge
del IWriteLock
