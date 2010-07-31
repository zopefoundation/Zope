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
"""
Transient Object Container Class ('timeslice'-based design, no index).
"""

from cgi import escape
from logging import getLogger
import math
import os
import random
import sys
import thread
import time

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SpecialUsers import nobody
from App.special_dtml import HTMLFile
from BTrees.Length import Length as BTreesLength
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from zope.interface import implements

from Products.Transience.TransienceInterfaces import DictionaryLike
from Products.Transience.TransienceInterfaces \
    import ImmutablyValuedMappingOfPickleableObjects
from Products.Transience.TransienceInterfaces import ItemWithId
from Products.Transience.TransienceInterfaces \
    import StringKeyedHomogeneousItemContainer
from Products.Transience.TransienceInterfaces import Transient
from Products.Transience.TransienceInterfaces import TransientItemContainer
from Products.Transience.TransienceInterfaces import TTWDictionary

from Products.Transience.TransientObject import TransientObject
from Products.Transience.Fake import FakeIOBTree

ADD_CONTAINER_PERM = 'Add Transient Object Container'
MGMT_SCREEN_PERM = 'View management screens'
ACCESS_CONTENTS_PERM = 'Access contents information'
CREATE_TRANSIENTS_PERM = 'Create Transient Objects'
ACCESS_TRANSIENTS_PERM = 'Access Transient Objects'
MANAGE_CONTAINER_PERM = 'Manage Transient Object Container'

SPARE_BUCKETS = 15 # minimum number of buckets to keep "spare"
BUCKET_CLASS = OOBTree # constructor for buckets
DATA_CLASS = IOBTree # const for main data structure (timeslice->"bucket")
STRICT = os.environ.get('Z_TOC_STRICT', '')
DEBUG = int(os.environ.get('Z_TOC_DEBUG', 0))

_marker = []
LOG = getLogger('Transience')

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
    LOG.info(msg)

constructTransientObjectContainerForm = HTMLFile(
    'dtml/addTransientObjectContainer', globals())

def constructTransientObjectContainer(self, id, title='', timeout_mins=20,
    addNotification=None, delNotification=None, limit=0, period_secs=20,
    REQUEST=None):
    """ """
    ob = TransientObjectContainer(id, title, timeout_mins,
        addNotification, delNotification, limit=limit, period_secs=period_secs)
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class MaxTransientObjectsExceeded(Exception): pass

class TransientObjectContainer(SimpleItem):
    """ Object which contains items that are automatically flushed
    after a period of inactivity """

    meta_type = "Transient Object Container"
    icon = "misc_/Transience/datacontainer.gif"

    implements(ItemWithId,
               StringKeyedHomogeneousItemContainer,
               TransientItemContainer,
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
    _inband_housekeeping = True

    security.setDefaultAccess('deny')

    # intitialize locks used for finalization, replentishing, and
    # garbage collection (used in _finalize, _replentish, and _gc
    # respectively)

    finalize_lock = thread.allocate_lock()
    replentish_lock =  thread.allocate_lock()
    gc_lock = thread.allocate_lock()

    def __init__(self, id, title='', timeout_mins=20, addNotification=None,
                 delNotification=None, limit=0, period_secs=20):
        self.id = id
        self.title=title
        self._setTimeout(timeout_mins, period_secs)
        self._setLimit(limit)
        self.setDelNotificationTarget(delNotification)
        self.setAddNotificationTarget(addNotification)
        self._reset()

    # helpers

    def _setTimeout(self, timeout_mins, period_secs):
        if type(timeout_mins) is not type(1):
            raise TypeError, (escape(`timeout_mins`), "Must be integer")

        if type(period_secs) is not type(1):
            raise TypeError, (escape(`period_secs`), "Must be integer")

        timeout_secs = timeout_mins * 60

        # special-case 0-minute timeout value by ignoring period
        if timeout_secs != 0:

            if period_secs == 0:
                raise ValueError('resolution cannot be 0')

            if period_secs > timeout_secs:
                raise ValueError(
                    'resolution cannot be greater than timeout '
                    'minutes * 60 ( %s > %s )' % (period_secs, timeout_secs))

            # we need the timeout to be evenly divisible by the period
            if timeout_secs % period_secs != 0:
                raise ValueError(
                    'timeout seconds (%s) must be evenly divisible '
                    'by resolution (%s)' % (timeout_secs, period_secs)
                    )

        # our timeout secs is the number of seconds that an item should
        # remain unexpired
        self._timeout_secs = timeout_secs

        # our _period is the number of seconds that constitutes a timeslice
        self._period = period_secs

        # timeout_slices == fewest number of timeslices that's >= timeout_secs
        self._timeout_slices=int(math.ceil(float(timeout_secs)/period_secs))

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
        # "get" calls), escaping expiration and eventual destruction only if
        # they move quickly enough.
        #
        # We make enough buckets initially to last us a while, and
        # we subsequently extend _data with fresh buckets and remove old
        # buckets as necessary during normal operations (see
        # _replentish() and _gc()).
        self._data = DATA_CLASS()

        # populate _data with some number of buckets, each of which
        # is "current" for its timeslice key
        if self._timeout_slices:
            new_slices = getTimeslices(
                getCurrentTimeslice(self._period),
                SPARE_BUCKETS*2,
                self._period)
            for i in new_slices:
                self._data[i] = BUCKET_CLASS()
            # max_timeslice is at any time during operations the highest
            # key value in _data.  Its existence is an optimization; getting
            # the maxKey of a BTree directly is read-conflict-prone.
            self._max_timeslice = Increaser(max(new_slices))
        else:
            self._data[0] = BUCKET_CLASS() # sentinel value for non-expiring
            self._max_timeslice = Increaser(0)

        # '_last_finalized_timeslice' is a value that indicates which
        # timeslice had its items last run through the finalization
        # process.  The finalization process calls the delete notifier for
        # each expired item.
        self._last_finalized_timeslice = Increaser(-self._period)

        # '_last_gc_timeslice' is a value that indicates in which
        # timeslice the garbage collection process was last run.
        self._last_gc_timeslice = Increaser(-self._period)
        
        # our "_length" is the number of "active" data objects in _data.
        # it does not include items that are still kept in _data but need to
        # be garbage collected.
        #
        # we need to maintain the length of the index structure separately
        # because getting the length of a BTree is very expensive, and it
        # doesn't really tell us which ones are "active" anyway.
        try:
            self._length.set(0)
        except AttributeError:
            self._length = self.getLen = Length2()

    def _getCurrentSlices(self, now):
        if self._timeout_slices:
            begin = now - (self._period * self._timeout_slices)
            # add add one to _timeout_slices below to account for the fact that
            # a call to this method may happen any time within the current
            # timeslice; calling it in the beginning of the timeslice can lead
            # to sessions becoming invalid a maximum of self._period seconds
            # earlier than the requested timeout value. Adding one here can
            # lead to sessions becoming invalid *later* than the timeout value
            # (also by a max of self._period), but in the common sessioning
            # case, that seems preferable.
            num_slices = self._timeout_slices + 1
        else:
            return [0] # sentinel for timeout value 0 (don't expire)
        DEBUG and TLOG('_getCurrentSlices, now = %s ' % now)
        DEBUG and TLOG('_getCurrentSlices, begin = %s' % begin)
        DEBUG and TLOG('_getCurrentSlices, num_slices = %s' % num_slices)
        result = getTimeslices(begin, num_slices, self._period)
        DEBUG and TLOG('_getCurrentSlices, result = %s' % result)
        return result

    def _move_item(self, k, current_ts, default=None):
        if not self._timeout_slices:
            # special case for no timeout value
            bucket = self._data.get(0)
            return bucket.get(k, default)

        if self._inband_housekeeping:
            self._housekeep(current_ts)

        else:
            # dont allow the TOC to stop working in an emergency bucket
            # shortage
            if self._in_emergency_bucket_shortage(current_ts):
                self._replentish(current_ts)

        # SUBTLETY ALERTY TO SELF: do not "improve" the code below
        # unnecessarily, as it will end only in tears.  The lack of aliases
        # and the ordering is intentional.

        STRICT and _assert(self._data.has_key(current_ts))
        current_slices = self._getCurrentSlices(current_ts)
        found_ts = None

        for ts in current_slices:
            abucket = self._data.get(ts, None) # XXX ReadConflictError hotspot

            if abucket is None:
                DEBUG and TLOG('_move_item: no bucket for ts %s' % ts)
                continue
            DEBUG and TLOG(
                '_move_item: bucket for ts %s is %s' % (ts, id(abucket)))
            DEBUG and TLOG(
                '_move_item: keys for ts %s (bucket %s)-- %s' %
                (ts, id(abucket), str(list(abucket.keys())))
                )
            # uhghost?
            if abucket.get(k, None) is not None:
                found_ts = ts
                break

        DEBUG and TLOG('_move_item: found_ts is %s' % found_ts)

        if found_ts is None:
            DEBUG and TLOG('_move_item: returning default of %s' % default)
            return default

        if found_ts != current_ts:

            DEBUG and TLOG('_move_item: current_ts (%s) != found_ts (%s), '
                           'moving to current' % (current_ts, found_ts))
            DEBUG and TLOG(
                '_move_item: keys for found_ts %s (bucket %s): %s' % (
                found_ts, id(self._data[found_ts]),
                `list(self._data[found_ts].keys())`)
                )
            self._data[current_ts][k] = self._data[found_ts][k]
            if not issubclass(BUCKET_CLASS, Persistent):
                # tickle persistence machinery
                self._data[current_ts] = self._data[current_ts]
            DEBUG and TLOG(
                '_move_item: copied item %s from %s to %s (bucket %s)' % (
                k, found_ts, current_ts, id(self._data[current_ts])))
            del self._data[found_ts][k]
            if not issubclass(BUCKET_CLASS, Persistent):
                # tickle persistence machinery
                self._data[found_ts] = self._data[found_ts]
            DEBUG and TLOG(
                '_move_item: deleted item %s from ts %s (bucket %s)' % (
                k, found_ts, id(self._data[found_ts]))
                )
            STRICT and _assert(self._data[found_ts].get(k, None) is None)
            STRICT and _assert(not self._data[found_ts].has_key(k))

        if getattr(self._data[current_ts][k], 'setLastAccessed', None):
            self._data[current_ts][k].setLastAccessed()
        DEBUG and TLOG('_move_item: returning %s from current_ts %s '
                       % (k, current_ts))
        return self._data[current_ts][k]

    def _all(self):
        if self._timeout_slices:
            current_ts = getCurrentTimeslice(self._period)
        else:
            current_ts = 0

        if self._inband_housekeeping:
            self._housekeep(current_ts)

        elif self._in_emergency_bucket_shortage(current_ts):
            # if our scheduler fails, dont allow the TOC to stop working
            self._replentish(current_ts, force=True)

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

    def raw(self, current_ts):
        # for debugging and unit testing
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
            current_ts = getCurrentTimeslice(self._period)
        else:
            current_ts = 0
        item = self._move_item(k, current_ts, _marker)
        STRICT and _assert(self._data.has_key(current_ts))

        if item is _marker:
            raise KeyError, k

        return self._wrap(item)

    def __setitem__(self, k, v):
        DEBUG and TLOG('__setitem__: called with key %s, value %s' % (k,v))
        if self._timeout_slices:
            current_ts = getCurrentTimeslice(self._period)
        else:
            current_ts = 0
        item = self._move_item(k, current_ts, _marker)
        STRICT and _assert(self._data.has_key(current_ts))
        if item is _marker:
            # the key didnt already exist, this is a new item

            length = self._length() # XXX ReadConflictError hotspot

            if self._limit and length >= self._limit:
                LOG.warn('Transient object container %s max subobjects '
                         'reached' % self.getId())
                    
                raise MaxTransientObjectsExceeded, (
                 "%s exceeds maximum number of subobjects %s" %
                 (length, self._limit))

            self._length.increment(1)

        DEBUG and TLOG('__setitem__: placing value for key %s in bucket %s' %
                       (k, current_ts))
        current_bucket = self._data[current_ts]
        current_bucket[k] = v
        if not issubclass(BUCKET_CLASS, Persistent):
            # tickle persistence machinery
            self._data[current_ts] = current_bucket
        self.notifyAdd(v)
        # change the TO's last accessed time
        # dont use hasattr here (it hides conflict errors)
        if getattr(v, 'setLastAccessed', None):
            v.setLastAccessed()

    def __delitem__(self, k):
        DEBUG and TLOG('__delitem__ called with key %s' % k)
        if self._timeout_slices:
            current_ts = getCurrentTimeslice(self._period)
        else:
            current_ts = 0
        item = self._move_item(k, current_ts)
        STRICT and _assert(self._data.has_key(current_ts))
        bucket = self._data[current_ts]
        del bucket[k]
        if not issubclass(BUCKET_CLASS, Persistent):
            # tickle persistence machinery
            self._data[current_ts] = bucket

        # XXX does increment(-1) make any sense here?
        # rationale from dunny: we are removing an item rather than simply
        # declaring it to be unused?
        self._length.increment(-1)
        return current_ts, item

    def __len__(self):
        return self._length()

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'get')
    def get(self, k, default=None):
        DEBUG and TLOG('get: called with key %s, default %s' % (k, default))
        if self._timeout_slices:
            current_ts = getCurrentTimeslice(self._period)
        else:
            current_ts = 0
        item = self._move_item(k, current_ts, default)
        STRICT and _assert(self._data.has_key(current_ts))
        if item is default:
            DEBUG and TLOG('get: returning default')
            return default
        return self._wrap(item)

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'has_key')
    def has_key(self, k):
        if self._timeout_slices:
            current_ts = getCurrentTimeslice(self._period)
        else:
            current_ts = 0
        DEBUG and TLOG('has_key: calling _move_item with %s' % str(k))
        item = self._move_item(k, current_ts, _marker)
        DEBUG and TLOG('has_key: _move_item returned %s%s' %
                       (item, item is _marker and ' (marker)' or ''))
        STRICT and _assert(self._data.has_key(current_ts))
        if item is not _marker:
            return True
        DEBUG and TLOG('has_key: returning false from for %s' % k)
        return False

    def _get_max_expired_ts(self, now):
        return now - (self._period * (self._timeout_slices + 1))

    def _in_emergency_bucket_shortage(self, now):
        max_ts = self._max_timeslice()
        low = now/self._period
        high = max_ts/self._period
        required = high <= low
        return required

    def _finalize(self, now):
        """ Call finalization handlers for the data in each stale bucket """
        if not self._timeout_slices:
            DEBUG and TLOG('_finalize: doing nothing (no timeout)')
            return # don't do any finalization if there is no timeout

        # The nature of sessioning is that when the timeslice rolls
        # over, all active threads will try to do a lot of work during
        # finalization if inband housekeeping is enabled, all but one
        # unnecessarily.  We really don't want more than one thread at
        # a time to try to finalize buckets at the same time so we try
        # to lock. We give up if we can't lock immediately because it
        # doesn't matter if we skip a couple of opportunities for
        # finalization, as long as it gets done by some thread
        # eventually.  A similar pattern exists for _gc and
        # _replentish.

        if not self.finalize_lock.acquire(0):
            DEBUG and TLOG('_finalize: could not acquire lock, returning')
            return

        try:
            DEBUG and TLOG('_finalize: lock acquired successfully')
            last_finalized = self._last_finalized_timeslice()

            # we want to start finalizing from one timeslice after the
            # timeslice which we last finalized.
            
            start_finalize  = last_finalized + self._period

            # we want to finalize only up to the maximum expired timeslice
            max_ts = self._get_max_expired_ts(now)

            if start_finalize >= max_ts:
                DEBUG and TLOG(
                    '_finalize: start_finalize (%s) >= max_ts (%s), '
                    'doing nothing' % (start_finalize, max_ts))
                return
            else:
                DEBUG and TLOG(
                    '_finalize: start_finalize (%s) <= max_ts (%s), '
                    'finalization possible' % (start_finalize, max_ts))
                # we don't try to avoid conflicts here by doing a "random"
                # dance (ala _replentish and _gc) because it's important that
                # buckets are finalized as soon as possible after they've
                # expired in order to call the delete notifier "on time".
                self._do_finalize_work(now, max_ts, start_finalize)

        finally:
            self.finalize_lock.release()

    def _do_finalize_work(self, now, max_ts, start_finalize):
        # this is only separated from _finalize for readability; it
        # should generally not be called by anything but _finalize
        DEBUG and TLOG('_do_finalize_work: entering')
        DEBUG and TLOG('_do_finalize_work: now is %s' % now)
        DEBUG and TLOG('_do_finalize_work: max_ts is %s' % max_ts)
        DEBUG and TLOG('_do_finalize_work: start_finalize is %s' %
                       start_finalize)

        to_finalize = list(self._data.keys(start_finalize, max_ts))
        DEBUG and TLOG('_do_finalize_work: to_finalize is %s' % `to_finalize`)

        delta = 0

        for key in to_finalize:

            _assert(start_finalize <= key)
            _assert(key <= max_ts)
            STRICT and _assert(self._data.has_key(key))
            values = list(self._data[key].values())
            DEBUG and TLOG('_do_finalize_work: values to notify from ts %s '
                           'are %s' % (key, `list(values)`))

            delta += len(values)

            for v in values:
                self.notifyDel(v)

        if delta:
            self._length.decrement(delta)

        DEBUG and TLOG('_do_finalize_work: setting _last_finalized_timeslice '
                       'to max_ts of %s' % max_ts)

        self._last_finalized_timeslice.set(max_ts)

    def _invoke_finalize_and_gc(self):
        # for unit testing purposes only!
        last_finalized = self._last_finalized_timeslice()
        now = getCurrentTimeslice(self._period) # for unit tests
        start_finalize  = last_finalized + self._period
        max_ts = self._get_max_expired_ts(now)
        self._do_finalize_work(now, max_ts, start_finalize)
        self._do_gc_work(now)

    def _replentish(self, now):
        """ Add 'fresh' future or current buckets """
        if not self._timeout_slices:
            DEBUG and TLOG('_replentish: no timeout, doing nothing')
            return
        
        # the difference between high and low naturally diminishes to
        # zero as now approaches self._max_timeslice() during normal
        # operations.  If high <= low, it means we have no current bucket,
        # so we *really* need to replentish (having a current bucket is
        # an invariant for continued operation).

        required = self._in_emergency_bucket_shortage(now)
        lock_acquired = self.replentish_lock.acquire(0)

        try:
            if required:
                # we're in an emergency bucket shortage, we need to
                # replentish regardless of whether we got the lock or
                # not.  (if we didn't get the lock, this transaction
                # will likely result in a conflict error, that's ok)
                if lock_acquired:
                    DEBUG and TLOG('_replentish: required, lock acquired)')
                else:
                    DEBUG and TLOG('_replentish: required, lock NOT acquired)')
                max_ts = self._max_timeslice()
                self._do_replentish_work(now, max_ts)

            elif lock_acquired:
                # If replentish is optional, minimize the chance that
                # two threads will attempt to do replentish work at
                # the same time (which causes conflicts) by
                # introducing a random element.
                DEBUG and TLOG('_replentish: attempting optional replentish '
                               '(lock acquired)')
                max_ts = self._max_timeslice()
                low = now/self._period
                high = max_ts/self._period
                if roll(low, high, 'optional replentish'):
                    self._do_replentish_work(now, max_ts)

            else:
                # This is an optional replentish and we can't acquire
                # the lock, bail.
                DEBUG and TLOG('_optional replentish attempt aborted, could '
                               'not acquire lock.')
                return

        finally:
            if lock_acquired:
                self.replentish_lock.release()

    def _do_replentish_work(self, now, max_ts):
        DEBUG and TLOG('_do_replentish_work: entering')
        # this is only separated from _replentish for readability; it
        # should generally not be called by anything but _replentish

        # available_spares == the number of "spare" buckets that exist
        # in "_data"
        available_spares = (max_ts - now) / self._period
        DEBUG and TLOG('_do_replentish_work: now = %s' % now)
        DEBUG and TLOG('_do_replentish_work: max_ts = %s' % max_ts)
        DEBUG and TLOG('_do_replentish_work: available_spares = %s'
                       % available_spares)

        if available_spares >= SPARE_BUCKETS:
            DEBUG and TLOG('_do_replentish_work: available_spares (%s) >= '
                           'SPARE_BUCKETS (%s), doing '
                           'nothing'% (available_spares,
                                       SPARE_BUCKETS))
            return

        if max_ts < now:
            # the newest bucket in self._data is older than now!
            replentish_start = now
            replentish_end = now + (self._period * SPARE_BUCKETS)

        else:
            replentish_start = max_ts + self._period
            replentish_end = max_ts + (self._period * (SPARE_BUCKETS +1))

        DEBUG and TLOG('_do_replentish_work: replentish_start = %s' %
                       replentish_start)
        DEBUG and TLOG('_do_replentish_work: replentish_end = %s'
                       % replentish_end)
        # n is the number of buckets to create
        n = (replentish_end - replentish_start) / self._period
        new_buckets = getTimeslices(replentish_start, n, self._period)
        new_buckets.reverse()
        STRICT and _assert(new_buckets)
        DEBUG and TLOG('_do_replentish_work: adding %s new buckets' % n)
        DEBUG and TLOG('_do_replentish_work: buckets to add = %s'
                       % new_buckets)
        for k in new_buckets:
            STRICT and _assert(not self._data.has_key(k))
            self._data[k] = BUCKET_CLASS() # XXX ReadConflictError hotspot

        self._max_timeslice.set(max(new_buckets))

    def _gc(self, now=None):
        """ Remove stale buckets """
        if not self._timeout_slices:
            return # dont do gc if there is no timeout

        # give callers a good chance to do nothing (gc isn't as important
        # as replentishment or finalization)
        if not roll(0, 5, 'gc'):
            DEBUG and TLOG('_gc: lost roll, doing nothing')
            return

        if not self.gc_lock.acquire(0):
            DEBUG and TLOG('_gc: couldnt acquire lock')
            return

        try: 
            if now is None:
                now = getCurrentTimeslice(self._period) # for unit tests

            last_gc = self._last_gc_timeslice()
            gc_every = self._period * round(SPARE_BUCKETS / 2.0)

            if (now - last_gc) < gc_every:
                DEBUG and TLOG('_gc: gc attempt not yet required '
                               '( (%s - %s) < %s )' % (now, last_gc, gc_every))
                return
            else:
                DEBUG and TLOG(
                    '_gc:  (%s -%s) > %s, gc invoked' % (now, last_gc,
                                                          gc_every))
                self._do_gc_work(now)

        finally:
            self.gc_lock.release()

    def _do_gc_work(self, now):
        # this is only separated from _gc for readability; it should
        # generally not be called by anything but _gc

        # we garbage collect any buckets that have already been run
        # through finalization
        DEBUG and TLOG('_do_gc_work: entering')

        max_ts = self._last_finalized_timeslice()

        DEBUG and TLOG('_do_gc_work: max_ts is %s' % max_ts)
        to_gc = list(self._data.keys(None, max_ts))
        DEBUG and TLOG('_do_gc_work: to_gc is: %s' % str(to_gc))

        for key in to_gc:
            _assert(key <= max_ts)
            STRICT and _assert(self._data.has_key(key))
            DEBUG and TLOG('_do_gc_work: deleting %s from _data' % key)
            del self._data[key]

        DEBUG and TLOG('_do_gc_work: setting last_gc_timeslice to %s' % now)
        self._last_gc_timeslice.set(now)

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
                err = 'No such onAdd/onDelete method %s referenced via %s'
                LOG.warn(err % (callback, '/'.join(path)),
                         exc_info=sys.exc_info())
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
                    LOG.warn('%s failed when calling %s in %s' % (name,callback,
                                                                 '/'.join(path)),
                             exc_info=sys.exc_info())
            finally:
                setSecurityManager(sm)
        else:
            err = '%s in %s attempted to call non-callable %s'
            path = self.getPhysicalPath()
            LOG.warn(err % (name, '/'.join(path), callback),
                     exc_info=sys.exc_info())

    def getId(self):
        return self.id

    security.declareProtected(CREATE_TRANSIENTS_PERM, 'new_or_existing')
    def new_or_existing(self, key):
        DEBUG and TLOG('new_or_existing called with %s' % key)
        item = self.get(key, _marker)
        if item is _marker:
            item = TransientObject(key)
            self[key] = item
            item = self._wrap(item)
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
        return self._wrap(item)

    # TransientItemContainer methods

    security.declareProtected(MANAGE_CONTAINER_PERM, 'setTimeoutMinutes')
    def setTimeoutMinutes(self, timeout_mins, period_secs=20):
        """ The period_secs parameter is defaulted to preserve backwards API
        compatibility.  In older versions of this code, period was
        hardcoded to 20. """
        timeout_secs = timeout_mins * 60
        
        if (timeout_mins != self.getTimeoutMinutes()
            or period_secs != self.getPeriodSeconds()):
            # do nothing unless something has changed
            self._setTimeout(timeout_mins, period_secs)
            self._reset()

    def getTimeoutMinutes(self):
        """ """
        return self._timeout_secs / 60

    def getPeriodSeconds(self):
        """ """
        return self._period

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

    security.declareProtected(MGMT_SCREEN_PERM, 'disableInbandHousekeeping')
    def disableInbandHousekeeping(self):
        """ No longer perform inband housekeeping """
        self._inband_housekeeping = False

    security.declareProtected(MGMT_SCREEN_PERM, 'enableInbandHousekeeping')
    def enableInbandHousekeeping(self):
        """ (Re)enable inband housekeeping """
        self._inband_housekeeping = True

    security.declareProtected(MGMT_SCREEN_PERM, 'isInbandHousekeepingEnabled')
    def isInbandHousekeepingEnabled(self):
        """ Report if inband housekeeping is enabled """
        return self._inband_housekeeping

    security.declareProtected('View', 'housekeep')
    def housekeep(self):
        """ Call this from a scheduler at least every
        self._period * (SPARE_BUCKETS - 1) seconds to perform out of band
        housekeeping """
        # we can protect this method from being called too often by
        # anonymous users as necessary in the future; we already have a lot
        # of protection as-is though so no need to make it more complicated
        # than necessary at the moment
        self._housekeep(getCurrentTimeslice(self._period))

    def _housekeep(self, now):
        self._finalize(now)
        self._replentish(now)
        self._gc(now)

    security.declareProtected(MANAGE_CONTAINER_PERM,
        'manage_changeTransientObjectContainer')
    def manage_changeTransientObjectContainer(
        self, title='', timeout_mins=20, addNotification=None,
        delNotification=None, limit=0, period_secs=20, REQUEST=None
        ):
        """ Change an existing transient object container. """
        self.title = title
        self.setTimeoutMinutes(timeout_mins, period_secs)
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
        
    def __setstate__(self, state):
        # upgrade versions of Transience in Zope versions less
        # than 2.7.1, which used a different transience mechanism.  Note:
        # this will not work for upgrading versions older than 2.6.0,
        # all of which used a very different transience implementation
        # can't make __len__ an instance variable in new-style classes

        # f/w compat: 2.8 cannot use __len__ as an instance variable
        if not state.has_key('_length'):
            length = state.get('__len__', Length2())
            self._length = self.getLen = length

        oldlength = state['_length']
        if isinstance(oldlength, BTreesLength):
            # TOCS prior to 2.7.3 had a BTrees.Length.Length object as
            # the TOC length object, replace it with our own Length2
            # that does our conflict resolution correctly:
            sz = oldlength()
            self._length = self.getLen = Length2(sz)

        # TOCs prior to 2.7.1 took their period from a global
        if not state.has_key('_period'):
            self._period = 20 # this was the default for all prior releases

        # TOCs prior to 2.7.1 used a different set of data structures
        # for efficiently keeping tabs on the maximum slice
        if not state.has_key('_max_timeslice'):
            new_slices = getTimeslices(
                getCurrentTimeslice(self._period),
                SPARE_BUCKETS*2,
                self._period)
            for i in new_slices:
                if not self._data.has_key(i):
                    self._data[i] = BUCKET_CLASS()
            # create an Increaser for max timeslice
            self._max_timeslice = Increaser(max(new_slices))

        if not state.has_key('_last_finalized_timeslice'):
            self._last_finalized_timeslice = Increaser(-self._period)

        # TOCs prior to 2.7.3 didn't have a _last_gc_timeslice
        if not state.has_key('_last_gc_timeslice'):
            self._last_gc_timeslice = Increaser(-self._period)

        # we should probably delete older attributes from state such as
        # '_last_timeslice', '_deindex_next',and '__len__' here but we leave
        # them in order to allow people to switch between 2.6.0->2.7.0 and
        # 2.7.1+ as necessary (although that has not been tested)
        self.__dict__.update(state)
    
def getCurrentTimeslice(period):
    """
    Return an integer representing the 'current' timeslice.
    The current timeslice is guaranteed to be the same integer
    within a 'slice' of time based on a divisor of 'self._period'.
    'self._period' is the number of seconds in a slice.
    """
    now = time.time()
    low = int(math.floor(now)) - period + 1
    high = int(math.ceil(now)) + 1
    for x in range(low, high):
        if x % period == 0:
            return x

def getTimeslices(begin, n, period):
    """ Get a list of future timeslice integers of 'n' size in descending
    order """
    l = []
    for x in range(n):
        l.insert(0, begin + (x * period))
    return l

def roll(low, high, reason):
    try:
        result = random.randrange(low, high)
    except ValueError:
        # empty range, must win this roll
        result = low

    if result == low:
        DEBUG and TLOG('roll: low: %s, high: %s: won with %s (%s)' %
                       (low, high, result, reason))
        return True
    else:
        DEBUG and TLOG('roll: low: %s, high: %s: lost with %s (%s)' %
                       (low, high, result, reason))
        return False

def _assert(case):
    if not case:
        raise AssertionError

class Increaser(Persistent):
    """
    A persistent object representing a typically increasing integer that
    has conflict resolution which uses the greatest integer out of the three
    available states.
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


class Length2(Persistent):
    """
    A persistent object responsible for maintaining a repesention of
    the number of current transient objects.

    Conflict resolution is sensitive to which methods are used to
    change the length.
    """
    def __init__(self, value=0):
        self.set(value)

    def set(self, value):
        self.value = value
        self.floor = 0
        self.ceiling = value

    def increment(self, delta):
        """Increase the length by delta.

        Conflict resolution will take the sum of all the increments."""
        self.ceiling += delta
        self.value += delta

    def decrement(self, delta):
        """Decrease the length by delta.

        Conflict resolution will take the highest decrement."""
        self.floor += delta
        self.value -= delta

    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, state):
        self.__dict__.update(state)

    def __call__(self):
        return self.value

    def _p_resolveConflict(self, old, saved, new):
        new['ceiling'] = saved['ceiling'] + new['ceiling'] - old['ceiling']
        new['floor'] = max(old['floor'], saved['floor'], new['floor'])
        new['value'] = new['ceiling'] - new['floor']
        return new

InitializeClass(TransientObjectContainer)

