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
Transient Object Container Class ('timeslice'-based design).

$Id: Transience.py,v 1.33 2003/11/18 13:17:08 tseaver Exp $
"""

__version__='$Revision: 1.33 $'[11:-2]

import Globals
from Globals import HTMLFile
from TransienceInterfaces import Transient, DictionaryLike, ItemWithId,\
     TTWDictionary, ImmutablyValuedMappingOfPickleableObjects,\
     StringKeyedHomogeneousItemContainer, TransientItemContainer
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from Acquisition import Implicit
from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import nobody
from BTrees.OOBTree import OOBTree, OOBucket, OOSet
from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from zLOG import LOG, WARNING, BLATHER
import os.path
import os
import math, sys, random
import time
from types import InstanceType
from TransientObject import TransientObject
import thread
import ThreadLock
import Queue
from cgi import escape

_marker = []

DEBUG = os.environ.get('Z_TOC_DEBUG', '')

class MaxTransientObjectsExceeded(Exception): pass

MIN_SPARE_BUCKETS = 10 # minimum number of transient buckets to keep spare
PERIOD = 20 # attempt housekeeping every PERIOD seconds
ADD_CONTAINER_PERM = 'Add Transient Object Container'
MGMT_SCREEN_PERM = 'View management screens'
ACCESS_CONTENTS_PERM = 'Access contents information'
CREATE_TRANSIENTS_PERM = 'Create Transient Objects'
ACCESS_TRANSIENTS_PERM = 'Access Transient Objects'
MANAGE_CONTAINER_PERM = 'Manage Transient Object Container'

constructTransientObjectContainerForm = HTMLFile(
    'dtml/addTransientObjectContainer', globals())

def TLOG(*args):
    sargs = []
    sargs.append(str(thread.get_ident()))
    sargs.append(str(time.time()))
    for arg in args:
        sargs.append(str(arg))
    LOG('Transience', BLATHER, ' '.join(sargs))

def constructTransientObjectContainer(self, id, title='', timeout_mins=20,
    addNotification=None, delNotification=None, limit=0, REQUEST=None):
    """ """
    ob = TransientObjectContainer(id, title, timeout_mins,
        addNotification, delNotification, limit=limit)
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class TransientObjectContainer(SimpleItem):
    """ Object which contains items that are automatically flushed
    after a period of inactivity """

    meta_type = "Transient Object Container"
    icon = "misc_/Transience/datacontainer.gif"

    # chrism 6/20/2002
    # I was forced to make this a mostly "synchronized" class, using
    # a single ThreadLock instance ("lock" below).   I realize this
    # is paranoid and even a little sloppy. ;-)
    #
    # Rationale: in high-conflict situations without this lock, the
    # index and the "data" (bucket) structure slowly get out of sync with
    # one another.  I'm only sure about one thing when it comes to this:
    # I don't completely understand why.  So, I'm not going to worry about
    # it (indefinitely) as the locking solves it. "Slow and steady" is better
    # than "fast and broken".
    lock = ThreadLock.allocate_lock()

    # notify_queue is a queue in which deindexed objects are placed
    # for later processing by housekeeping, which calls the
    # "delete notifier" at appropriate times.  As threads pass through
    # the housekeeping stage, they pull any unnotified objects from this
    # queue and call the delete notifier.  We use a queue here in order
    # to not "double-notify" when two threads are doing housekeeping
    # at the same time.  Note that there may be a case where a conflict
    # error is raised and the results of a delete notifier are not
    # committed, but that is better than calling the delete notifier
    # *again* on the retry.
    notify_queue = Queue.Queue()

    # replentish queue is a size-one queue.   It is used as optimization
    # to avoid conflicts. If you're running low on buckets, an entry is
    # placed in the replentish queue.  The next thread that does housekeeping
    # to notice the entry will extend the buckets.  Because queues are thread-
    # safe, more than one thread will not attempt to replentish at the same
    # time.
    replentish_queue = Queue.Queue(1)

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
        self._reset()
        self._setTimeout(timeout_mins)
        self._setLimit(limit)
        self._addCallback = None
        self._delCallback = None
        self.setDelNotificationTarget(delNotification)
        self.setAddNotificationTarget(addNotification)

    security.declareProtected(CREATE_TRANSIENTS_PERM, 'new_or_existing')
    def new_or_existing(self, key):
        self.lock.acquire()
        try:
            DEBUG and TLOG('new_or_existing called with %s' % key)
            notfound = []
            item  = self.get(key, notfound)
            if item is notfound:
                # intentionally dont call "new" here in order to avoid another
                # call to "get"
                item = TransientObject(key)
                self[key] = item
                self.notifyAdd(item)
            return item.__of__(self)
        finally:
            self.lock.release()

    security.declareProtected(CREATE_TRANSIENTS_PERM, 'new')
    def new(self, key):
        self.lock.acquire()
        try:
            if type(key) is not type(''):
                raise TypeError, (key, "key is not a string type")
            if self.has_key(key):
                raise KeyError, "cannot duplicate key %s" % key
            item = TransientObject(key)
            self[key] = item
            self.notifyAdd(item)
            return item.__of__(self)
        finally:
            self.lock.release()

    security.declareProtected(MANAGE_CONTAINER_PERM, 'setTimeoutMinutes')
    def setTimeoutMinutes(self, timeout_mins):
        """ """
        if timeout_mins != self.getTimeoutMinutes():
            self._setTimeout(timeout_mins)
            self._reset()

    security.declareProtected(MGMT_SCREEN_PERM, 'getTimeoutMinutes')
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
        # We should assert that the callback function 'f' implements
        # the TransientNotification interface
        self._addCallback = f

    security.declareProtected(MGMT_SCREEN_PERM, 'getDelNotificationTarget')
    def getDelNotificationTarget(self):
        return self._delCallback or ''

    security.declareProtected(MANAGE_CONTAINER_PERM,'setDelNotificationTarget')
    def setDelNotificationTarget(self, f):
        # We should assert that the callback function 'f' implements
        # the TransientNotification interface
        self._delCallback = f

    def notifyAdd(self, item):
        if self._addCallback:
            self._notify(item, 'add')

    def notifyDestruct(self, item):
        if self._delCallback:
            self._notify(item, 'destruct')

    def _notify(self, items, kind):
        if not type(items) in [type([]), type(())]:
            items = [items]

        if kind =='add':
            name = 'notifyAdd'
            callback = self._addCallback
        else:
            name = 'notifyDestruct'
            callback = self._delCallback
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

        for item in items:
            if callable(method):
                try:
                    user = getSecurityManager().getUser()
                    try:
                        newSecurityManager(None, nobody)
                        method(item, self)
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
                    newSecurityManager(None, user)
            else:
                err = '%s in %s attempted to call non-callable %s'
                path = self.getPhysicalPath()
                LOG('Transience',
                    WARNING,
                    err % (name, '/'.join(path), callback),
                    error=sys.exc_info()
                    )

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

    def _setTimeout(self, timeout_mins):
        if type(timeout_mins) is not type(1):
            raise TypeError, (escape(`timeout_mins`), "Must be integer")
        self._timeout_secs = t_secs = timeout_mins * 60
        # timeout_slices == fewest number of timeslices that's >= t_secs
        self._timeout_slices=int(math.ceil(float(t_secs)/self._period))

    def _setLimit(self, limit):
        if type(limit) is not type(1):
            raise TypeError, (escape(`limit`), "Must be integer")
        self._limit = limit

    security.declareProtected(MGMT_SCREEN_PERM, 'nudge')
    def nudge(self):
        """ Used by mgmt interface to maybe turn the ring each time
        a screen is shown """
        self._getCurrentBucket()

    def _getCurrentTimeslice(self):
        """
        Return an integer representing the 'current' timeslice.
        The current timeslice is guaranteed to be the same integer
        within a 'slice' of time based on a divisor of 'period'.
        'period' is the number of seconds in a slice.
        """
        period = self._period
        now = time.time()
        low = int(math.floor(now)) - period + 1
        high = int(math.ceil(now)) + 1
        for x in range(low, high):
            if x % period == 0:
                return x

    def _getTimeslices(self, begin, n):
        """ Get a list of future timeslice integers of 'n' size """
        l = []
        for x in range(n):
            l.append(begin + (x * self._period))
        return l

    def _getIndex(self):
        """ returns the index, a mapping of TOC key to bucket """
        self.lock.acquire()
        try:
            if self._data is None:
                # do in-place upgrade of old instances
                self._upgrade()
            return self._index
        finally:
            self.lock.release()

    def _upgrade(self):
        """ upgrade older ring-based (2.5.X) TOC instances """
        self.lock.acquire()
        try:
            self._reset()
            timeout_mins = self._timeout_secs / 60
            self._setTimeout(timeout_mins)
            # iterate over all the buckets in the ring
            for bucket, dump_after in self._ring._data:
                # get all TOs in the ring and call our __setitem__
                for k, v in bucket.items():
                    self[k] = v
            # we probably should delete the old "_ring" attribute here,
            # but leave it around in case folks switch back to 2.5.X
        finally:
            self.lock.release()

    def _reset(self):
        """ Reset ourselves to a sane state (deletes all content) """
        self.lock.acquire()
        try:
            # set the period (the timeslice length)
            self._period = PERIOD

            # set the number of minimum spare buckets
            self._min_spare_buckets = MIN_SPARE_BUCKETS

            # _data contains a mapping of f-of-time(int) (aka "slice") to
            # "bucket".  Each bucket will contain a set of transient items.
            # Transient items move automatically from bucket-to-bucket inside
            # of the _data structure based on last access time (e.g.
            # "get" calls), escaping destruction only if they move quickly
            # enough.
            # We make enough buckets initially to last us a while, and
            # we subsequently extend _data with fresh buckets and remove old
            # buckets as necessary during normal operations (see
            # _housekeep()).
            self._data = IOBTree()

            # populate _data with some number of buckets, each of which
            # is "current" for its timeslice key
            for i in self._getTimeslices(self._getCurrentTimeslice(),
                                         self._min_spare_buckets*2):
                self._data[i] = OOBTree()

            # _index is a mapping of transient item key -> slice, letting
            # us quickly figure out which bucket in the _data mapping
            # contains the transient object related to the key
            self._index = OOBTree()

            # our "__len__" is the length of _index.
            # we need to maintain the length of the index structure separately
            # because getting the length of a BTree is very expensive.
            try: self.__len__.set(0)
            except AttributeError: self.__len__ = self.getLen = Length()

            # set up last_timeslice and deindex_next integer pointers
            # we set them to the current timeslice as it's the only sane
            # thing to do
            self._last_timeslice=Increaser(self._getCurrentTimeslice())
            self._deindex_next=Increaser(self._getCurrentTimeslice())
        finally:
            self.lock.release()

    def _getCurrentBucket(self):
        """
        Do housekeeping if necessary, then return the 'current' bucket.
        """
        self.lock.acquire()
        try:
            # do in-place upgrade of old "ring-based" instances if
            # we've just upgraded from Zope 2.5.X
            if self._data is None:
                self._upgrade()

            # data is the mapping from timeslice to bucket
            data = self._data

            # period == number of seconds in a slice
            period = self._period
            
            # pnow == the current timeslice
            pnow = self._getCurrentTimeslice()

            # pprev = the true previous timeslice in relation to pnow
            pprev = pnow - period

            # plast == the last timeslice under which we did housekeeping
            plast = self._last_timeslice()

            if not data.has_key(pnow):
                # we were asleep a little too long, we don't even have a
                # current bucket; we create one for ourselves.
                # XXX - currently this ignores going back in time.
                DEBUG and TLOG('_getCurrentBucket: creating current bucket!')
                data[pnow] = OOBTree()

            if pnow <= plast:
                # If we went "back in time" or if the timeslice hasn't
                # changed, dont try to do housekeeping.
                # Instead, just return the current bucket.
                return pnow

            # the current timeslice has changed since the last time we did
            # housekeeping, so we're going to see if we need to finalize
            # anything.
            DEBUG and TLOG('_getCurrentBucket: new timeslice (pnow) %s' % pnow)

            # pmax == the last timeslice integer kept by _data as a key.
            pmax = data.maxKey()

            # t_slices == this TOC's timeout expressed in slices
            # (fewest number of timeslices that's >= t_secs)
            t_slices = self._timeout_slices

            # deindex_next == the timeslice of the bucket we need to start
            # deindexing from
            deindex_next = self._deindex_next()

            # The ordered set implied by data.keys(deindex_next, pprev) is
            # a set of all timeslices that may have entries in the index which
            # are known about by _data, starting from "deindex_next" up to
            # but not including the current timeslice.  We iterate over
            # these keys, deindexing buckets as necessary when they're older
            # than the timeout.
            # XXX - fixme!  range search doesn't always work (btrees bug)
            for k in list(data.keys(deindex_next, pprev)):
                if k < deindex_next:
                    DEBUG and TLOG(
                        'broken range search: key %s < min %s'
                        % (k, deindex_next)
                        )
                    continue
                if k > pprev:
                    DEBUG and TLOG(
                        'broken range search: key %s > max %s'
                        % (k, pprev)
                        )
                    continue

                # pthen == the number of seconds elapsed since the timeslice
                # implied by k
                pthen = pnow - k

                # slices_since == the number of slices elapsed since the
                # timeslice implied by k
                slices_since = pthen / self._period

                # if the number of slices since 'k' is less than the number of
                # slices that make up the timeout, break out of this loop.
                # (remember, this is an ordered set, and following keys are
                # bound to be higher, meaning subsequent tests will also fail,
                # so we don't even bother checking them)
                if slices_since < t_slices:
                    DEBUG and TLOG(
                        '_getCurrentBucket: slices_since (%s)<t_slices (%s)' %
                        (slices_since, t_slices))
                    break

                # if the bucket has keys, deindex them and add them to the
                # notify queue (destruction notification happens during
                # garbage collection)
                bucket = data.get(k, _marker)
                if bucket is _marker:
                    DEBUG and TLOG(
                        'data IOBTree lied about keys: %s doesnt exist' % k
                        )
                    continue
                
                keys = list(bucket.keys())
                for key in keys:
                    ob = bucket.get(key, _marker)
                    if ob is _marker:
                        DEBUG and TLOG(
                            'bucket OOBTree lied about keys: %s doesnt exist' %
                            key
                            )
                        continue
                    self.notify_queue.put((key, ob))
                DEBUG and TLOG(
                    '_getCurrentBucket: deindexing keys %s' % keys
                    )
                keys and self._deindex(keys)
                # set the "last deindexed" pointer to k + period
                deindex_next = k+period
                self._deindex_next.set(deindex_next)

            # housekeep_elected indicates that this thread was elected to do
            # housekeeping.  We set it off initially and only set it true if
            # we "win the roll". The "roll" is necessary to avoid a conflict
            # scenario where more than one thread tries to do housekeeping at
            # the same time.
            housekeep_elected = 0

            # We ask this thread to "roll the dice." If it wins, it gets
            # elected to do housekeeping
            housekeep_elected = self._roll(pnow, pmax)
            housekeep_elected and DEBUG and TLOG('housekeep elected')

            # if we were elected to do housekeeping, do it now.
            if housekeep_elected:

                # available_spares == the number of "spare" ("clean", "future")
                # buckets that exist in "_data"
                available_spares = (pmax-pnow) / period
                DEBUG and TLOG(
                    '_getCurrentBucket: available_spares %s' % available_spares
                    )

                # delete_end == the last bucket we want to destroy
                delete_end = deindex_next - period

                # min_spares == minimum number of spare buckets acceptable
                # by this TOC
                min_spares = self._min_spare_buckets

                if available_spares < min_spares:
                    DEBUG and TLOG(
                        '_getCurrentBucket: available_spares < min_spares'
                        )
                    # the first bucket we want to begin creating
                    replentish_start = pmax + period
                    try:
                        self.replentish_queue.put_nowait(replentish_start)
                    except Queue.Full:
                        DEBUG and TLOG(
                            '_getCurrentBucket: replentish queue full'
                            )
                self._housekeep(delete_end)

            # finally, bump the last_timeslice housekeeping counter and return
            # the current bucket
            self._last_timeslice.set(pnow)
            return pnow
        finally:
            self.lock.release()

    def _roll(self, pnow, pmax):
        """
        Roll the dice to see if we're the lucky thread that does
        housekeeping.  This method is guaranteed to return true at
        some point as the difference between pnow and pmax naturally
        diminishes to zero.

        The reason we do the 'random' dance in the last part of this
        is to minimize the chance that two threads will attempt to
        do housekeeping at the same time (causing conflicts and double-
        notifications).
        """
        period = self._period
        low = pnow/period
        high = pmax/period
        if high <= low:
            # we really need to win this roll because we have no
            # spare buckets (and no valid values to provide to randrange), so
            # we rig the toss.
            DEBUG and TLOG("_roll: rigged toss")
            return 1
        else:
            # we're not in an emergency bucket shortage, so we can take
            # our chances during the roll.  It's highly unlikely that two
            # threads will win the roll simultaneously, so we avoid a certain
            # class of conflicts here.
            if random.randrange(low, high) == low: # WINNAH!
                DEBUG and TLOG("_roll: roll winner")
                return 1
        DEBUG and TLOG("_roll: roll loser")
        return 0

    def _housekeep(self, delete_end):
        """ do garbage collection, bucket replentishing and notification """
        data = self._data
        period = self._period
        min_spares = self._min_spare_buckets
        DEBUG and TLOG(
            '_housekeep: current slice %s' % self._getCurrentTimeslice()
            )
        notify = {}
        while 1:
            try:
                k, v = self.notify_queue.get_nowait()
                # duplicates will be ignored
                notify[k] = v
            except Queue.Empty:
                break

        to_notify = notify.values()
        # if we have transient objects to notify about destruction, notify
        # them (only once, that's why we use a queue) ("notification")
        if to_notify:
            DEBUG and TLOG('_housekeep: notifying: %s' % notify.keys())
            self.notifyDestruct(to_notify)

        # extend _data with extra buckets if necessary ("bucket replentishing")
        try:
            replentish_start = self.replentish_queue.get_nowait()
            DEBUG and TLOG('_housekeep: replentishing')
            new_bucket_keys=self._getTimeslices(replentish_start, min_spares)
            DEBUG and TLOG('_housekeep: new_bucket_keys = %s '%new_bucket_keys)
            for i in new_bucket_keys:
                if data.has_key(i):
                    continue
                data[i] = OOBTree()
        except Queue.Empty:
            DEBUG and TLOG('replentish queue empty')

        # gc the stale buckets at the "beginning" of _data ("garbage collect")
        # iterate over the keys in data that have no minimum value and
        # a maximum value of delete_end (note: ordered set)
        # XXX- fixme.  range search doesn't always work (btrees bug)
        for k in list(data.keys(None, delete_end)):
            if k > delete_end:
                DEBUG and TLOG(
                    '_housekeep: broken range search (key %s > max %s)'
                    % (k, delete_end)
                    )
                continue
            bucket = data.get(k, _marker)
            if bucket is _marker:
                DEBUG and TLOG(
                    'bucket OOBTree lied about keys: %s doesnt exist' % k
                    )
                continue
            # delete the bucket from _data
            del data[k]
            DEBUG and TLOG('_housekeep: deleted data[%s]' % k)

    def _deindex(self, keys):
        """ Iterate over 'keys' and remove any that match from our index """
        self.lock.acquire()
        try:
            index = self._getIndex()
            for k in keys:
                if index.has_key(k):
                    DEBUG and TLOG('_deindex: deleting %s' % k)
                    self.__len__.change(-1)
                    del index[k]
        finally:
            self.lock.release()

    def __setitem__(self, k, v):
        self.lock.acquire()
        try:
            notfound = []
            current = self._getCurrentBucket()
            index = self._getIndex()
            b = index.get(k, notfound)
            if b is notfound:
                # if this is a new item, we do OOM protection before actually
                # adding it to ourselves.
                li = self._limit
                if li and len(self) >= li:
                    LOG('Transience', WARNING,
                        ('Transient object container %s max subobjects '
                         'reached' % self.id)
                        )
                    raise MaxTransientObjectsExceeded, (
                     "%s exceeds maximum number of subobjects %s" %
                     (len(self), li))
                # do length accounting
                try: self.__len__.change(1)
                except AttributeError: pass
            elif b != current:
                # this is an old key that isn't in the current bucket.
                if self._data[b].has_key(k):
                    del self._data[b][k] # delete it from the old bucket

            # change the value
            DEBUG and TLOG('setitem: setting current[%s]=%s' % (k,v))
            self._data[current][k] = v
            # change the TO's last accessed time
            if hasattr(v, 'setLastAccessed'):
                v.setLastAccessed()
            # set the index up with the current bucket for this key
            index[k] = current

        finally:
            self.lock.release()

    def __getitem__(self, k):
        self.lock.acquire()
        try:
            # we dont want to call getCurrentBucket here because we need to
            # be able to raise a KeyError.  The housekeeping steps
            # performed in the getCurrentBucket method would be ignored
            # if we raised a KeyError.
            index = self._getIndex()
            # the next line will raise the proper error if the item has expired
            b = index[k]
            v = self._data[b][k]
            if hasattr(v, '__of__'):
                return v.__of__(self)
            else:
                return v
        finally:
            self.lock.release()

    def __delitem__(self, k):
        self.lock.acquire()
        try:
            self._getCurrentBucket()
            index = self._getIndex()
            b = index[k]
            v = self._data[b][k]
            del self._data[b][k]
            self.__len__.change(-1)
            if hasattr(v, '__of__'):
                v = v.__of__(self)
            del index[k]
        finally:
            self.lock.release()
        self.notifyDestruct(v)


    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'get')
    def get(self, k, default=_marker):
        self.lock.acquire()
        try:
            DEBUG and TLOG('get: called with k=%s' % k)
            notfound = []
            current = self._getCurrentBucket()
            DEBUG and TLOG('get: current is %s' % current)
            if default is _marker: default=None
            index = self._getIndex()
            b = index.get(k, notfound)
            if b is notfound:
                # it's not here, this is a genuine miss
                DEBUG and TLOG('bucket was notfound for %s' %k)
                return default
            else:
                v = self._data[b].get(k, notfound)
                if v is notfound:
                    DEBUG and TLOG(
                        'get: %s was not found in index bucket (%s)' % (k, b))
                    return default
                elif b != current:
                    DEBUG and TLOG('get: b was not current, it was %s' %b)
                    # we accessed the object, so it becomes current
                    # by moving it to the current bucket
                    del self._data[b][k] # delete the item from the old bucket.
                    self._data[current][k] = v # add the value to the current
                    self._setLastAccessed(v)
                    index[k] = current # change the index to the current buck.

                if hasattr(v, '__of__'):
                    v = v.__of__(self)
                return v
        finally:
            self.lock.release()

    def _setLastAccessed(self, transientObject):
        self.lock.acquire()
        try:
            sla = getattr(transientObject, 'setLastAccessed', None)
            if sla is not None: sla()
        finally:
            self.lock.release()

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'has_key')
    def has_key(self, k):
        notfound = []
        v = self.get(k, notfound)
        if v is notfound: return 0
        return 1

    def values(self):
        # sloppy and loving it!
        # we used to use something like:
        # [ self[x] for x in self.keys() ]
        # but it was causing KeyErrors in getitem's "v = self._data[b][k]"
        # due to some synchronization problem that I don't understand.
        # since this is a utility method, I don't care too much. -cm
        l = []
        notfound = []
        for k, t in self._index.items():
            bucket = self._data.get(t, notfound)
            if bucket is notfound:
                continue
            value = bucket.get(k, notfound)
            if value is notfound:
                continue
            if hasattr(value, '__of__'):
                value = value.__of__(self)
            l.append(value)
        return l

    def items(self):
        # sloppy and loving it!
        # we used to use something like:
        # [ (x, self[x]) for x in self.keys() ]
        # but it was causing KeyErrors in getitem's "v = self._data[b][k]"
        # due to some synchronization problem that I don't understand.
        # since this is a utility method, I don't care too much. -cm
        l = []
        notfound = []
        for k, t in self._index.items():
            bucket = self._data.get(t, notfound)
            if bucket is notfound:
                continue
            value = bucket.get(k, notfound)
            if value is notfound:
                continue
            if hasattr(value, '__of__'):
                value = value.__of__(self)
            l.append((k, value))
        return l

    def true_items(self):
        l = []
        for bucket in self._data.values():
            items = list(bucket.items())
            l.extend(items)
        return l

    def keys(self):
        self._getCurrentBucket()
        index = self._getIndex()
        return list(index.keys())

    # proxy security declaration
    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'getLen')

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
        DEBUG and TLOG('Resolving conflict in Increaser')
        if old <= state1 <= state2: return state2
        if old <= state2 <= state1: return state1
        return old

    def _p_independent(self):
        return 1

class Ring(Persistent):
    """ ring of buckets.  This class is only kept for backwards-compatibility
    purposes (Zope 2.5X). """
    def __init__(self, l, index):
        if not len(l):
            raise ValueError, "ring must have at least one element"
        DEBUG and TLOG('initial _ring buckets: %s' % map(oid, l))
        self._data = l
        self._index = index

    def __repr__(self):
        return repr(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, i):
        return self._data[i]

    def turn(self):
        last = self._data.pop(-1)
        self._data.insert(0, last)
        self._p_changed = 1

    def _p_independent(self):
        return 1

Globals.InitializeClass(TransientObjectContainer)
