##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Simple ZODB-based transient object implementation.
"""

import logging
import os
import random
import sys
import thread
import time

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from Persistence import Persistent
from ZODB.POSException import ConflictError
from zope.interface import implements

from Products.Transience.TransienceInterfaces import DictionaryLike
from Products.Transience.TransienceInterfaces import \
                        ImmutablyValuedMappingOfPickleableObjects
from Products.Transience.TransienceInterfaces import ItemWithId
from Products.Transience.TransienceInterfaces import Transient
from Products.Transience.TransienceInterfaces import TransientItemContainer
from Products.Transience.TransienceInterfaces import TTWDictionary

DEBUG = int(os.environ.get('Z_TOC_DEBUG', 0))
LOG = logging.getLogger('Zope.TransientObject')

def TLOG(*args):
    sargs = []
    sargs.append(str(thread.get_ident()))
    sargs.append(str(time.time()))
    for arg in args:
        sargs.append(str(arg))
    msg = ' '.join(sargs)
    LOG.info(msg)

_notfound = []

WRITEGRANULARITY=30 # Timing granularity for access write clustering, seconds

class TransientObject(Persistent, Implicit):
    """ Dictionary-like object that supports additional methods
    concerning expiration and containment in a transient object container
    """
    implements(ItemWithId, # randomly generate an id
               Transient,
               DictionaryLike,
               TTWDictionary,
               ImmutablyValuedMappingOfPickleableObjects
              )

    security = ClassSecurityInfo()
    security.setDefaultAccess('allow')
    security.declareObjectPublic()
    _last_modified = None
    # _last modified indicates the last time that __setitem__, __delitem__,
    # update or clear was called on us.

    def __init__(self, containerkey):
        self.token = containerkey
        self.id = self._generateUniqueId()
        self._container = {}
        self._created = self._last_accessed = time.time()
        # _last_accessed indicates the last time that *our container
        # was asked about us* (NOT the last time __getitem__ or get
        # or any of our other invariant data access methods are called).
        # Our container manages our last accessed time, we don't much
        # concern ourselves with it other than exposing an interface
        # to set it on ourselves.

    # -----------------------------------------------------------------
    # ItemWithId
    #

    def getId(self):
        return self.id

    # -----------------------------------------------------------------
    # Transient
    #

    def invalidate(self):
        # hasattr hides conflicts
        if getattr(self, '_invalid', _notfound) is not _notfound:
            # we dont want to invalidate twice
            return
        trans_ob_container = None
        # search our acquisition chain for a transient object container
        # and delete ourselves from it.
        for ob in getattr(self, 'aq_chain', []):
            if TransientItemContainer.providedBy(ob):
                trans_ob_container = ob
                break
        if trans_ob_container is not None:
            if trans_ob_container.has_key(self.token):
                del trans_ob_container[self.token]
        self._invalid = None

    def isValid(self):
        # hasattr hides conflicts
        if getattr(self, '_invalid', _notfound) is _notfound:
            return 1

    def getLastAccessed(self):
        return self._last_accessed

    def setLastAccessed(self):
        # check to see if the last_accessed time is too recent, and avoid
        # setting if so, to cut down on heavy writes
        t = time.time()
        if (self._last_accessed + WRITEGRANULARITY) < t:
            self._last_accessed = t

    def getLastModified(self):
        return self._last_modified

    def setLastModified(self):
        self._last_modified = time.time()

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
        self._p_changed = 1
        self._container.clear()
        self.setLastModified()

    def update(self, d):
        self._p_changed = 1
        for k in d.keys():
            self[k] = d[k]

    # -----------------------------------------------------------------
    # ImmutablyValuedMappingOfPickleableObjects (what a mouthful!)
    #

    def __setitem__(self, k, v):
        self._p_changed = 1
        self._container[k] = v
        self.setLastModified()

    def __getitem__(self, k):
        return self._container[k]

    def __delitem__(self, k):
        self._p_changed = 1
        del self._container[k]
        self.setLastModified()

    # -----------------------------------------------------------------
    # TTWDictionary
    #

    set = __setitem__
    __guarded_setitem__ = __setitem__
    __guarded_delitem__ = __delitem__
    delete = __delitem__

    # -----------------------------------------------------------------
    # Other non interface code
    #

    def _p_resolveConflict(self, saved, state1, state2):
        DEBUG and TLOG('entering TO _p_rc')
        DEBUG and TLOG('states: sv: %s, s1: %s, s2: %s' % (
            saved, state1, state2))
        states = [saved, state1, state2]

        # We can clearly resolve the conflict if one state is invalid,
        # because it's a terminal state.
        for state in states:
            if state.has_key('_invalid'):
                DEBUG and TLOG('TO _p_rc: a state was invalid')
                return state

        # The only other times we can clearly resolve the conflict is if
        # the token, the id, or the creation time don't differ between
        # the three states, so we check that here.  If any differ, we punt
        # by raising ConflictError.
        attrs = ['token', 'id', '_created']
        for attr in attrs:
            svattr = saved.get(attr)
            s1attr = state1.get(attr)
            s2attr = state2.get(attr)
            DEBUG and TLOG('TO _p_rc: attr %s: sv: %s s1: %s s2: %s' %
                           (attr, svattr, s1attr, s2attr))
            if not svattr==s1attr==s2attr:
                DEBUG and TLOG('TO _p_rc: cant resolve conflict')
                raise ConflictError

        # Now we need to do real work.
        #
        # Data in our _container dictionaries might conflict.  To make
        # things simple, we intentionally create a race condition where the
        # state which was last modified "wins".  It would be preferable to
        # somehow merge our _containers together, but as there's no
        # generally acceptable way to union their states, there's not much
        # we can do about it if we want to be able to resolve this kind of
        # conflict.

        # We return the state which was most recently modified, if
        # possible.
        states.sort(lastmodified_sort)
        if states[0].get('_last_modified'):
            DEBUG and TLOG('TO _p_rc: returning last mod state')
            return states[0]

        # If we can't determine which object to return on the basis
        # of last modification time (no state has been modified), we return
        # the object that was most recently accessed (last pulled out of
        # our parent).  This will return an essentially arbitrary state if
        # all last_accessed values are equal.
        states.sort(lastaccessed_sort)
        DEBUG and TLOG('TO _p_rc: returning last_accessed state')
        return states[0]

    getName = getId # this is for SQLSession compatibility

    def _generateUniqueId(self):
        t = str(int(time.time()))
        d = "%010d" % random.randint(0, sys.maxint-1)
        return "%s%s" % (t, d)

    def __repr__(self):
        return "id: %s, token: %s, content keys: %s" % (
            self.id, self.token, `self.keys()`
            )

def lastmodified_sort(d1, d2):
    """ sort dictionaries in descending order based on last mod time """
    m1 = d1.get('_last_modified', 0)
    m2 = d2.get('_last_modified', 0)
    if m1 == m2: return 0
    if m1 > m2: return -1 # d1 is "less than" d2
    return 1

def lastaccessed_sort(d1, d2):
    """ sort dictionaries in descending order based on last access time """
    m1 = d1.get('_last_accessed', 0)
    m2 = d2.get('_last_accessed', 0)
    if m1 == m2: return 0
    if m1 > m2: return -1 # d1 is "less than" d2
    return 1

InitializeClass(TransientObject)
