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

__version__ = "$Revision: 1.3 $"[11:-2]

from string import lower, split, join
from Globals import Persistent
from WriteLockInterface import LockItemInterface
from AccessControl import ClassSecurityInfo
from AccessControl.Owned import ownerInfo
from common import generateLockToken
import time

MAXTIMEOUT = (2L**32)-1                 # Maximum timeout time
DEFAULTTIMEOUT = 12 * 60L               # Default timeout

def validateTimeout(timeout):
    # Timeout *should* be in the form "Seconds-XXX" or "Infinite"
    errors = []
    try:
        t = split(str(timeout), '-')[-1]
        if lower(t) == 'infinite':
            timeout = DEFAULTTIMEOUT # Default to 1800 secods for infinite
        else:                       # requests
            timeout = long(t)
    except ValueError:
        errors.append("Bad timeout value")
    if timeout > MAXTIMEOUT:
        errors.append("Timeout request is greater than %s" % MAXTIMEOUT)
    return timeout, errors


class LockItem(Persistent):
    __implements__ = (LockItemInterface,)

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
        if lower(str(depth)) not in ('0', 'infinity'):
            errors.append("Depth must be 0 or infinity")
        if lower(locktype) != 'write':
            errors.append("Lock type '%s' not supported" % locktype)
        if lower(lockscope) != 'exclusive':
            errors.append("Lock scope '%s' not supported" % lockscope)

        timeout, e = validateTimeout(timeout)
        errors = errors + e

        # Finally, if there were errors, report them ALL to on high
        if errors:
            raise ValueError, errors

        # AccessControl.Owned.ownerInfo returns the id of the creator
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
        path = join(db,'/')
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

    def asLockDiscoveryProperty(self, ns='d'):
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
               'locktoken': self._token,
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
    
