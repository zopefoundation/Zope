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
"""
Simple ZODB-based transient object implementation.

$Id: TransientObject.py,v 1.2 2001/11/26 15:29:27 chrism Exp $
"""

__version__='$Revision: 1.2 $'[11:-2]

from Persistence import Persistent
from Acquisition import Implicit
import time, random, sys
from TransienceInterfaces import ItemWithId, Transient, DictionaryLike,\
     TTWDictionary, ImmutablyValuedMappingOfPickleableObjects
from AccessControl import ClassSecurityInfo
import Globals
from zLOG import LOG, BLATHER

_notfound = []

WRITEGRANULARITY=30     # Timing granularity for write clustering, in seconds

class TransientObject(Persistent, Implicit):
    """ Dictionary-like object that supports additional methods
    concerning expiration and containment in a transient object container
    """
    __implements__ = (ItemWithId, # randomly generate an id
                      Transient,
                      DictionaryLike,
                      TTWDictionary,
                      ImmutablyValuedMappingOfPickleableObjects
                      )

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')
    security.declareObjectPublic()

    def __init__(self, containerkey):
        self.token = containerkey
        self.id = self._generateUniqueId()
        self._container = {}
        self._created = self._last_accessed = time.time()

    # -----------------------------------------------------------------
    # ItemWithId
    #

    def getId(self):
        return self.id

    # -----------------------------------------------------------------
    # Transient
    #

    def invalidate(self):
        self._invalid = None

    def isValid(self):
        return not hasattr(self, '_invalid')

    def getLastAccessed(self):
        return self._last_accessed

    def setLastAccessed(self, WG=WRITEGRANULARITY):
        # check to see if the last_accessed time is too recent, and avoid
        # setting if so, to cut down on heavy writes
        t = time.time()
        if (self._last_accessed + WG) < t:
            self._last_accessed = t

    def getCreated(self):
        return self._created

    def getContainerKey(self):
        return self.token
    
    # -----------------------------------------------------------------
    # DictionaryLike
    #

    def keys(self):
        return self._container.keys()

    def values(self):
        return self._container.values()

    def items(self):
        return self._container.items()

    def get(self, k, default=_notfound):
        v = self._container.get(k, default)
        if v is _notfound: return None
        return v
        
    def has_key(self, k):
        if self._container.get(k, _notfound) is not _notfound: return 1
        return 0

    def clear(self):
        self._container.clear()
        self._p_changed = 1

    def update(self, d):
        for k in d.keys():
            self[k] = d[k]

    # -----------------------------------------------------------------
    # ImmutablyValuedMappingOfPickleableObjects (what a mouthful!)
    #

    def __setitem__(self, k, v):
        # if the key or value is a persistent instance,
        # set up its _p_jar immediately
        if hasattr(v, '_p_jar') and v._p_jar is None:
            v._p_jar = self._p_jar
            v._p_changed = 1
        if hasattr(k, '_p_jar') and k._p_jar is None:
            k._p_jar = self._p_jar
            k._p_changed = 1
        self._container[k] = v
        self._p_changed = 1

    def __getitem__(self, k):
        return self._container[k]

    def __delitem__(self, k):
        del self._container[k]

    # -----------------------------------------------------------------
    # TTWDictionary
    #

    set = __setitem__

    def delete(self, k):
        del self._container[k]
        self._p_changed = 1
        
    __guarded_setitem__ = __setitem__

    # -----------------------------------------------------------------
    # Other non interface code
    #

    def _p_independent(self):
        # My state doesn't depend on or materially effect the state of
        # other objects (eliminates read conflicts).
        return 1

    def _p_resolveConflict(self, saved, state1, state2):
        attrs = ['token', 'id', '_created', '_invalid']
        # note that last_accessed and _container are the only attrs
        # missing from this list.  The only time we can clearly resolve
        # the conflict is if everything but the last_accessed time and
        # the contents are the same, so we make sure nothing else has
        # changed.  We're being slightly sneaky here by accepting
        # possibly conflicting data in _container, but it's acceptable
        # in this context.
        LOG('Transience', BLATHER, 'Resolving conflict in TransientObject')
        for attr in attrs:
            old = saved.get(attr)
            st1 = state1.get(attr)
            st2 = state2.get(attr)
            if not (old == st1 == st2):
                return None
        # return the object with the most recent last_accessed value.
        if state1['_last_accessed'] > state2['_last_accessed']:
            return state1
        else:
            return state2

    getName = getId # this is for SQLSession compatibility

    def _generateUniqueId(self):
        t = str(int(time.time()))
        d = "%010d" % random.randint(0, sys.maxint-1)
        return "%s%s" % (t, d)

    def __repr__(self):
        return "id: %s, token: %s, contents: %s" % (
            self.id, self.token, `self.items()`
            )

Globals.InitializeClass(TransientObject)
