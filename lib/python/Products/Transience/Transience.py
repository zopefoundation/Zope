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
"""
Transient Object Container Class ('timeslice'-based design, no index).

$Id: Transience.py,v 1.32.12.3 2004/05/14 22:52:12 chrism Exp $
"""

__version__='$Revision: 1.32.12.3 $'[11:-2]

import math
import time
import random
import sys
import os
import thread
from cgi import escape

import Globals
from Globals import HTMLFile
from TransienceInterfaces import Transient, DictionaryLike, ItemWithId,\
     TTWDictionary, ImmutablyValuedMappingOfPickleableObjects,\
     StringKeyedHomogeneousItemContainer, TransientItemContainer

from BTrees.Length import Length
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from ZODB.POSException import ConflictError

from Persistence import Persistent
from OFS.SimpleItem import SimpleItem
from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager, \
     setSecurityManager
from AccessControl.User import nobody
from zLOG import LOG, WARNING, BLATHER

from TransientObject import TransientObject

ADD_CONTAINER_PERM = 'Add Transient Object Container'
MGMT_SCREEN_PERM = 'View management screens'
ACCESS_CONTENTS_PERM = 'Access contents information'
CREATE_TRANSIENTS_PERM = 'Create Transient Objects'
ACCESS_TRANSIENTS_PERM = 'Access Transient Objects'
MANAGE_CONTAINER_PERM = 'Manage Transient Object Container'

PERIOD = 20 # signifies "resolution" of transience machinery
SPARE_BUCKETS = 15 # number of buckets to keep spare
STRICT = os.environ.get('Z_TOC_STRICT', '')
DEBUG = int(os.environ.get('Z_TOC_DEBUG', 0))

_marker = []

def setStrict(on=''):
    """ Turn on assertions (which may cause conflicts) """
    global STRICT
    STRICT = on

def TLOG(*args):
    sargs = []
    sargs.append(str(thread.get_ident()))
    sargs.append(str(time.time()))
    for arg in args:
        sargs.append(str(arg))
    msg = ' '.join(sargs)
    LOG('Transience', BLATHER, msg)

constructTransientObjectContainerForm = HTMLFile(
    'dtml/addTransientObjectContainer', globals())

def constructTransientObjectContainer(self, id, title='', timeout_mins=20,
    addNotification=None, delNotification=None, limit=0, REQUEST=None):
    """ """
    ob = TransientObjectContainer(id, title, timeout_mins,
        addNotification, delNotification, limit=limit)
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class MaxTransientObjectsExceeded(Exception): pass

class TransientObjectContainer(SimpleItem):
    """ Object which contains items that are automatically flushed
    after a period of inactivity """

    meta_type = "Transient Object Container"
    icon = "misc_/Transience/datacontainer.gif"

    __implements__ = (ItemWithId,
                      StringKeyedHomogeneousItemContainer,
                      TransientItemContainer
                      )
    manage_options = (
        {   'label':    'Manage',
            'action':   'manage_container',
            'help':     ('Transience', 'Transience.stx')
        },
        {   'label':    'Security',
            'action':   'manage_access'
        },
    )

    security = ClassSecurityInfo()
    security.setPermissionDefault(MANAGE_CONTAINER_PERM,
                                ['Manager',])
    security.setPermissionDefault(MGMT_SCREEN_PERM,
                                ['Manager',])
    security.setPermissionDefault(ACCESS_CONTENTS_PERM,
                                ['Manager','Anonymous'])
    security.setPermissionDefault(ACCESS_TRANSIENTS_PERM,
                                ['Manager','Anonymous','Sessions'])
    security.setPermissionDefault(CREATE_TRANSIENTS_PERM,
                                ['Manager',])

    security.declareProtected(MGMT_SCREEN_PERM, 'manage_container')
    manage_container = HTMLFile('dtml/manageTransientObjectContainer',
        globals())

    _limit = 0
    _data = None

    security.setDefaultAccess('deny')

    def __init__(self, id, title='', timeout_mins=20, addNotification=None,
                 delNotification=None, limit=0):
        self.id = id
        self.title=title
        self._setTimeout(timeout_mins)
        self._setLimit(limit)
        self.setDelNotificationTarget(delNotification)
        self.setAddNotificationTarget(addNotification)
        self._reset()

    # helpers

    def _setTimeout(self, timeout_mins):
        if type(timeout_mins) is not type(1):
            raise TypeError, (escape(`timeout_mins`), "Must be integer")
        self._timeout_secs = t_secs = timeout_mins * 60
        # timeout_slices == fewest number of timeslices that's >= t_secs
        self._timeout_slices=int(math.ceil(float(t_secs)/PERIOD))

    def _setLimit(self, limit):
        if type(limit) is not type(1):
            raise TypeError, (escape(`limit`), "Must be integer")
        self._limit = limit

    def _reset(self):
        """ Reset ourselves to a sane state (deletes all content) """
        # _data contains a mapping of f-of-time(int) (aka "slice") to
        # "bucket".  Each bucket will contain a set of transient items.
        # Transient items move automatically from bucket-to-bucket inside
        # of the _data structure based on last access time (e.g.
        # "get" calls), escaping destruction only if they move quickly
        # enough.
        # We make enough buckets initially to last us a while, and
        # we subsequently extend _data with fresh buckets and remove old
        # buckets as necessary during normal operations (see
        # _gc() and _replentish()).
        self._data = IOBTree()

        # populate _data with some number of buckets, each of which
        # is "current" for its timeslice key
        if self._timeout_slices:
            new_slices = getTimeslices(getCurrentTimeslice(), SPARE_BUCKETS*2)
            for i in new_slices:
                self._data[i] = OOBTree()
            # create an Increaser for max timeslice
            self._max_timeslice = Increaser(max(new_slices))
        else:
            self._data[0] = OOBTree() # sentinel value for non-expiring data
            self._max_timeslice = Increaser(0)

        # our "_length" is the length of _index.
        # we need to maintain the length of the index structure separately
        # because getting the length of a BTree is very expensive.
        try: self._length.set(0)
        except AttributeError: self._length = self.getLen = Length()

    def _getCurrentSlices(self, now):
        if self._timeout_slices:
            begin = now+PERIOD - (PERIOD * self._timeout_slices)
            num_slices = self._timeout_slices
        else:
            return [0] # sentinel for timeout value 0 (don't expire)
        DEBUG and TLOG('_getCurrentSlices, begin = %s' % begin)
        DEBUG and TLOG('_getCurrentSlices, num_slices = %s' % num_slices)
        result = getTimeslices(begin, num_slices)
        DEBUG and TLOG('_getCurrentSlices, result = %s' % result)
        return result

    def _move_item(self, k, current_ts, default=None):
        if not getattr(self, '_max_timeslice', None):
            # in-place upgrade for old instances; this would usually be
            # "evil" but sessions are all about write-on-read anyway,
            # so it really doesn't matter.
            self._upgrade()

        if self._timeout_slices:

            if self._roll(current_ts, 'replentish'):
                self._replentish(current_ts)

            if self._roll(current_ts, 'gc'):
                self._gc(current_ts)

            STRICT and _assert(self._data.has_key(current_ts))
            current = self._getCurrentSlices(current_ts)
            found_ts = None

            for ts in current:
                bucket = self._data.get(ts)
                # dont use hasattr here (it hides conflict errors)
                if getattr(bucket, 'has_key', None) and bucket.has_key(k):
                    found_ts = ts
                    break

            if found_ts is None:
                return default

            bucket = self._data[found_ts]
            item = bucket[k]

            if current_ts != found_ts:
                del bucket[k]
                self._data[current_ts][k] = item

        else:
            # special case for no timeout value
            bucket = self._data.get(0)
            item = bucket.get(k, default)

        # dont use hasattr here (it hides conflict errors)
        if getattr(item, 'setLastAccessed', None):
            item.setLastAccessed()
        return item

    def _all(self):
        if not getattr(self, '_max_timeslice', None):
            # in-place upgrade for old instances
            self._upgrade()

        if self._timeout_slices:
            current_ts = getCurrentTimeslice()
        else:
            current_ts = 0

        if self._roll(current_ts, 'replentish'):
            self._replentish(current_ts)

        if self._roll(current_ts, 'gc'):
            self._gc(current_ts)

        STRICT and _assert(self._data.has_key(current_ts))
        current = self._getCurrentSlices(current_ts)

        current.reverse() # overwrite older with newer

        d = {}
        for ts in current:
            bucket = self._data.get(ts)
            if bucket is None:
                continue
            for k,v in bucket.items():
                d[k] = self._wrap(v)

        return d

    def keys(self):
        return self._all().keys()

    def rawkeys(self, current_ts):
        # for debugging
        current = self._getCurrentSlices(current_ts)

        current.reverse() # overwrite older with newer

        d = {}
        for ts in current:
            bucket = self._data.get(ts, None)
            if bucket is None:
                continue
            for k,v in bucket.items():
                d[k] = self._wrap(v)

        return d

    def items(self):
        return self._all().items()

    def values(self):
        return self._all().values()

    def _wrap(self, item):
        # dont use hasattr here (it hides conflict errors)
        if getattr(item, '__of__', None):
            item = item.__of__(self)
        return item

    def __getitem__(self, k):
        if self._timeout_slices:
            current_ts = getCurrentTimeslice()
        else:
            current_ts = 0
        item = self._move_item(k, current_ts, _marker)
        STRICT and _assert(self._data.has_key(current_ts))

        if item is _marker:
            raise KeyError, k

        return self._wrap(item)

    def __setitem__(self, k, v):
        if self._timeout_slices:
            current_ts = getCurrentTimeslice()
        else:
            current_ts = 0
        item = self._move_item(k, current_ts, _marker)
        STRICT and _assert(self._data.has_key(current_ts))
        if item is _marker:
            # the key didnt already exist, this is a new item
            if self._limit and len(self) >= self._limit:
                LOG('Transience', WARNING,
                    ('Transient object container %s max subobjects '
                     'reached' % self.getId())
                    )
                raise MaxTransientObjectsExceeded, (
                 "%s exceeds maximum number of subobjects %s" %
                 (len(self), self._limit))
            self._length.change(1)
        current_bucket = self._data[current_ts]
        current_bucket[k] = v
        self.notifyAdd(v)
        # change the TO's last accessed time
        # dont use hasattr here (it hides conflict errors)
        if getattr(v, 'setLastAccessed', None):
            v.setLastAccessed()

    def __delitem__(self, k):
        if self._timeout_slices:
            current_ts = getCurrentTimeslice()
        else:
            current_ts = 0
        item = self._move_item(k, current_ts)
        STRICT and _assert(self._data.has_key(current_ts))
        del self._data[current_ts][k]
        self._length.change(-1)
        return current_ts, item

    def __len__(self):
        return self._length()

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'get')
    def get(self, k, default=None):
        if self._timeout_slices:
            current_ts = getCurrentTimeslice()
        else:
            current_ts = 0
        item = self._move_item(k, current_ts, _marker)
        STRICT and _assert(self._data.has_key(current_ts))
        if item is _marker:
            return default
        return self._wrap(item)

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'has_key')
    def has_key(self, k):
        if self._timeout_slices:
            current_ts = getCurrentTimeslice()
        else:
            current_ts = 0
        item = self._move_item(k, current_ts, _marker)
        STRICT and _assert(self._data.has_key(current_ts))
        if item is not _marker:
            return True
        return False

    def _roll(self, now, reason):
        """
        Roll the dice to see if we're the lucky thread that does
        bucket replentishment or gc.  This method is guaranteed to return
        true at some point as the difference between high and low naturally
        diminishes to zero.

        The reason we do the 'random' dance in the last part of this
        is to minimize the chance that two threads will attempt to
        do housekeeping at the same time (causing conflicts).
        """
        low = now/PERIOD
        high = self._max_timeslice()/PERIOD
        if high <= low:
            # we really need to win this roll because we have no
            # spare buckets (and no valid values to provide to randrange), so
            # we rig the toss.
            DEBUG and TLOG('_roll: %s rigged toss' % reason)
            return True
        else:
            # we're not in an emergency bucket shortage, so we can take
            # our chances during the roll.  It's highly unlikely that two
            # threads will win the roll simultaneously, so we avoid a certain
            # class of conflicts here.
            if random.randrange(low, high) == low: # WINNAH!
                DEBUG and TLOG("_roll: %s roll winner" % reason)
                return True
        DEBUG and TLOG("_roll: %s roll loser" % reason)
        return False

    def _replentish(self, now):
        # available_spares == the number of "spare" buckets that exist in
        # "_data"
        if not self._timeout_slices:
            return # do nothing if no timeout
        
        max_ts = self._max_timeslice()
        available_spares = (max_ts-now) / PERIOD
        DEBUG and TLOG('_replentish: now = %s' % now)
        DEBUG and TLOG('_replentish: max_ts = %s' % max_ts)
        DEBUG and TLOG('_replentish: available_spares = %s'
                       % available_spares)

        if available_spares < SPARE_BUCKETS:
            if max_ts < now:
                replentish_start = now
                replentish_end = now + (PERIOD * SPARE_BUCKETS)

            else:
                replentish_start = max_ts + PERIOD
                replentish_end = max_ts + (PERIOD * SPARE_BUCKETS)

            DEBUG and TLOG('_replentish: replentish_start = %s' %
                           replentish_start)
            DEBUG and TLOG('_replentish: replentish_end = %s'
                           % replentish_end)
            # n is the number of buckets to create
            n = (replentish_end - replentish_start) / PERIOD
            new_buckets = getTimeslices(replentish_start, n)
            new_buckets.reverse()
            STRICT and _assert(new_buckets)
            DEBUG and TLOG('_replentish: adding %s new buckets' % n)
            DEBUG and TLOG('_replentish: buckets to add = %s'
                           % new_buckets)
            for k in new_buckets:
                STRICT and _assert(not self._data.has_key(k))
                try:
                    self._data[k] = OOBTree()
                except ConflictError:
                    DEBUG and TLOG('_replentish: conflict when adding %s' % k)
                    time.sleep(random.choice([0.1, 0.2, 0.3])) # add entropy
                    raise
            self._max_timeslice.set(max(new_buckets))

    def _gc(self, now=None):
        if not self._timeout_slices:
            return # dont do gc if there is no timeout

        if now is None:
            now = getCurrentTimeslice() # for unit tests
        max_ts = now  - (PERIOD * (self._timeout_slices + 1))

        to_notify = []

        for key in list(self._data.keys(None, max_ts)):
            assert(key <= max_ts)
            STRICT and _assert(self._data.has_key(key))

            for v in self._data[key].values():
                to_notify.append(v)
                self._length.change(-1)

            del self._data[key]

        for v in to_notify:
            self.notifyDel(v)

    def notifyAdd(self, item):
        DEBUG and TLOG('notifyAdd with %s' % item)
        callback = self._getCallback(self._addCallback)
        if callback is None:
            return
        self._notify(item, callback, 'notifyAdd')

    def notifyDel(self, item):
        DEBUG and TLOG('notifyDel with %s' % item)
        callback = self._getCallback(self._delCallback)
        if callback is None:
            return
        self._notify(item, callback, 'notifyDel' )

    def _getCallback(self, callback):
        if not callback:
            return None
        if type(callback) is type(''):
            try:
                method = self.unrestrictedTraverse(callback)
            except (KeyError, AttributeError):
                path = self.getPhysicalPath()
                err = 'No such method %s in %s %s'
                LOG('Transience',
                    WARNING,
                    err % (callback, '/'.join(path), name),
                    error=sys.exc_info()
                    )
                return
        else:
            method = callback
        return method

    def _notify(self, item, callback, name):
        if callable(callback):
            sm = getSecurityManager()
            try:
                user = sm.getUser()
                try:
                    newSecurityManager(None, nobody)
                    callback(item, self)
                except:
                    # dont raise, just log
                    path = self.getPhysicalPath()
                    LOG('Transience',
                        WARNING,
                        '%s failed when calling %s in %s' % (name,callback,
                                                        '/'.join(path)),
                        error=sys.exc_info()
                        )
            finally:
                setSecurityManager(sm)
        else:
            err = '%s in %s attempted to call non-callable %s'
            path = self.getPhysicalPath()
            LOG('Transience',
                WARNING,
                err % (name, '/'.join(path), callback),
                error=sys.exc_info()
                )

    def getId(self):
        return self.id

    security.declareProtected(CREATE_TRANSIENTS_PERM, 'new_or_existing')
    def new_or_existing(self, key):
        DEBUG and TLOG('new_or_existing called with %s' % key)
        item = self.get(key, _marker)
        if item is _marker:
            item = TransientObject(key)
            self[key] = item
            item = item.__of__(self)
        return item

    security.declareProtected(CREATE_TRANSIENTS_PERM, 'new')
    def new(self, key):
        DEBUG and TLOG('new called with %s' % key)
        if type(key) is not type(''):
            raise TypeError, (key, "key is not a string type")
        if self.has_key(key):
            raise KeyError, "cannot duplicate key %s" % key
        item = TransientObject(key)
        self[key] = item
        return item.__of__(self)

    # TransientItemContainer methods

    security.declareProtected(MANAGE_CONTAINER_PERM, 'setTimeoutMinutes')
    def setTimeoutMinutes(self, timeout_mins):
        """ """
        if timeout_mins != self.getTimeoutMinutes():
            self._setTimeout(timeout_mins)
            self._reset()

    def getTimeoutMinutes(self):
        """ """
        return self._timeout_secs / 60

    security.declareProtected(MGMT_SCREEN_PERM, 'getSubobjectLimit')
    def getSubobjectLimit(self):
        """ """
        return self._limit

    security.declareProtected(MANAGE_CONTAINER_PERM, 'setSubobjectLimit')
    def setSubobjectLimit(self, limit):
        """ """
        if limit != self.getSubobjectLimit():
            self._setLimit(limit)

    security.declareProtected(MGMT_SCREEN_PERM, 'getAddNotificationTarget')
    def getAddNotificationTarget(self):
        return self._addCallback or ''

    security.declareProtected(MANAGE_CONTAINER_PERM,'setAddNotificationTarget')
    def setAddNotificationTarget(self, f):
        self._addCallback = f

    security.declareProtected(MGMT_SCREEN_PERM, 'getDelNotificationTarget')
    def getDelNotificationTarget(self):
        return self._delCallback or ''

    security.declareProtected(MANAGE_CONTAINER_PERM,'setDelNotificationTarget')
    def setDelNotificationTarget(self, f):
        self._delCallback = f

    security.declareProtected(MGMT_SCREEN_PERM, 'nudge')
    def nudge(self):
        """ Used by mgmt interface to maybe do housekeeping each time
        a screen is shown """
        # run garbage collector so view is correct
        self._gc()

    security.declareProtected(MANAGE_CONTAINER_PERM,
        'manage_changeTransientObjectContainer')
    def manage_changeTransientObjectContainer(
        self, title='', timeout_mins=20, addNotification=None,
        delNotification=None, limit=0, REQUEST=None
        ):
        """ Change an existing transient object container. """
        self.title = title
        self.setTimeoutMinutes(timeout_mins)
        self.setSubobjectLimit(limit)
        if not addNotification:
            addNotification = None
        if not delNotification:
            delNotification = None
        self.setAddNotificationTarget(addNotification)
        self.setDelNotificationTarget(delNotification)

        if REQUEST is not None:
            return self.manage_container(
                self, REQUEST, manage_tabs_message='Changes saved.'
                )
        
    def _upgrade(self):
        # inplace upgrade for versions of Transience in Zope versions less
        # than 2.7.1, which used a different transience mechanism.  Note:
        # this will not work for upgrading versions older than 2.6.0,
        # all of which used a very different transience implementation
        if not getattr(self, '_max_timeslice', None):
            new_slices = getTimeslices(getCurrentTimeslice(), SPARE_BUCKETS*2)
            for i in new_slices:
                if not self._data.has_key(i):
                    self._data[i] = OOBTree()
            # create an Increaser for max timeslice
            self._max_timeslice = Increaser(max(new_slices))

        # can't make __len__ an instance variable in new-style classes
        if not getattr(self, '_length', None):
            length = self.__dict__.get('__len__', Length())
            self._length = self.getLen = length

        # we should probably delete older attributes such as
        # '_last_timeslice', '_deindex_next',and '__len__' here but we leave
        # them in order to allow people to switch between 2.6.0->2.7.0 and
        # 2.7.1+ as necessary (although that has not been tested)
    
def getCurrentTimeslice():
    """
    Return an integer representing the 'current' timeslice.
    The current timeslice is guaranteed to be the same integer
    within a 'slice' of time based on a divisor of 'period'.
    'period' is the number of seconds in a slice.
    """
    now = time.time()
    low = int(math.floor(now)) - PERIOD + 1
    high = int(math.ceil(now)) + 1
    for x in range(low, high):
        if x % PERIOD == 0:
            return x

def getTimeslices(begin, n):
    """ Get a list of future timeslice integers of 'n' size in descending
    order """
    l = []
    for x in range(n):
        l.insert(0, begin + (x * PERIOD))
    return l

def _assert(case):
    if not case:
        raise AssertionError

class Increaser(Persistent):
    """
    A persistent object representing a typically increasing integer that
    has conflict resolution uses the greatest integer out of the three
    available states
    """
    def __init__(self, v):
        self.value = v

    def set(self, v):
        self.value = v

    def __getstate__(self):
        return self.value

    def __setstate__(self, v):
        self.value = v

    def __call__(self):
        return self.value

    def _p_resolveConflict(self, old, state1, state2):
        return max(old, state1, state2)

    def _p_independent(self):
        return 1

Globals.InitializeClass(TransientObjectContainer)
