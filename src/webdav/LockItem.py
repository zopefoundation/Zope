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
"""WebDAV support - lock item.
"""

import time

from AccessControl.class_init import InitializeClass
from AccessControl.owner import ownerInfo
from AccessControl.SecurityInfo import ClassSecurityInfo
from Persistence import Persistent
from zope.interface import implements

from webdav.common import generateLockToken
from webdav.interfaces import ILockItem

MAXTIMEOUT = (2L**32)-1                 # Maximum timeout time
DEFAULTTIMEOUT = 12 * 60L               # Default timeout

def validateTimeout(timeout):
    # Timeout *should* be in the form "Seconds-XXX" or "Infinite"
    errors = []
    try:
        t =str(timeout).split('-')[-1]
        if t.lower() == 'infinite':
            timeout = DEFAULTTIMEOUT # Default to 1800 secods for infinite
        else:                       # requests
            timeout = long(t)
    except ValueError:
        errors.append("Bad timeout value")
    if timeout > MAXTIMEOUT:
        errors.append("Timeout request is greater than %s" % MAXTIMEOUT)
    return timeout, errors


class LockItem(Persistent):

    implements(ILockItem)

    # Use the Zope 2.3 declarative security to manage access
    security = ClassSecurityInfo()
    security.declarePublic('getOwner', 'getLockToken', 'getDepth',
                           'getTimeout', 'getTimeoutString',
                           'getModifiedTime', 'isValid', 'getLockScope',
                           'getLockType')
    security.declareProtected('Change Lock Information',
                              'setTimeout', 'refresh')
    security.declareProtected('Access contents information',
                              'getCreator', 'getCreatorPath')

    def __init__(self, creator, owner='', depth=0, timeout='Infinite',
                 locktype='write', lockscope='exclusive', token=None):
        errors = []
        # First check the values and raise value errors if outside of contract
        if not getattr(creator, 'getUserName', None):
            errors.append("Creator not a user object")
        if str(depth).lower() not in ('0', 'infinity'):
            errors.append("Depth must be 0 or infinity")
        if locktype.lower() != 'write':
            errors.append("Lock type '%s' not supported" % locktype)
        if lockscope.lower() != 'exclusive':
            errors.append("Lock scope '%s' not supported" % lockscope)

        timeout, e = validateTimeout(timeout)
        errors = errors + e

        # Finally, if there were errors, report them ALL to on high
        if errors:
            raise ValueError, errors

        # AccessControl.owner.ownerInfo returns the id of the creator
        # and the path to the UserFolder they're defined in
        self._creator = ownerInfo(creator)

        self._owner = owner
        self._depth = depth
        self._timeout = timeout
        self._locktype = locktype
        self._lockscope = lockscope
        self._modifiedtime = time.time()

        if token is None:
            self._token = generateLockToken()
        else:
            self._token = token

    def getCreator(self):
        return self._creator

    def getCreatorPath(self):
        db, name = self._creator
        path = '/'.join(db)
        return "/%s/%s" % (path, name)

    def getOwner(self):
        return self._owner

    def getLockToken(self):
        return self._token

    def getDepth(self):
        return self._depth

    def getTimeout(self):
        return self._timeout

    def getTimeoutString(self):
        t = str(self._timeout)
        if t[-1] == 'L': t = t[:-1]     # lob off Long signifier
        return "Second-%s" % t

    def setTimeout(self, newtimeout):
        timeout, errors = validateTimeout(newtimeout)
        if errors:
            raise ValueError, errors
        else:
            self._timeout = timeout
            self._modifiedtime = time.time() # reset modified

    def getModifiedTime(self):
        return self._modifiedtime

    def refresh(self):
        self._modifiedtime = time.time()

    def isValid(self):
        now = time.time()
        modified = self._modifiedtime
        timeout = self._timeout

        return (modified + timeout) > now

    def getLockType(self):
        return self._locktype

    def getLockScope(self):
        return self._lockscope

    def asLockDiscoveryProperty(self, ns='d',fake=0):

        if fake: token = 'this-is-a-faked-no-permission-token'
        else:    token = self._token
        s = (' <%(ns)s:activelock>\n'
             '  <%(ns)s:locktype><%(ns)s:%(locktype)s/></%(ns)s:locktype>\n'
             '  <%(ns)s:lockscope><%(ns)s:%(lockscope)s/></%(ns)s:lockscope>\n'
             '  <%(ns)s:depth>%(depth)s</%(ns)s:depth>\n'
             '  <%(ns)s:owner>%(owner)s</%(ns)s:owner>\n'
             '  <%(ns)s:timeout>%(timeout)s</%(ns)s:timeout>\n'
             '  <%(ns)s:locktoken>\n'
             '   <%(ns)s:href>opaquelocktoken:%(locktoken)s</%(ns)s:href>\n'
             '  </%(ns)s:locktoken>\n'
             ' </%(ns)s:activelock>\n'
             ) % {
               'ns': ns,
               'locktype': self._locktype,
               'lockscope': self._lockscope,
               'depth': self._depth,
               'owner': self._owner,
               'timeout': self.getTimeoutString(),
               'locktoken': token,
               }
        return s

    def asXML(self):
        s = """<?xml version="1.0" encoding="utf-8" ?>
<d:prop xmlns:d="DAV:">
 <d:lockdiscovery>
  %s
 </d:lockdiscovery>
</d:prop>""" % self.asLockDiscoveryProperty(ns="d")
        return s

InitializeClass(LockItem)
