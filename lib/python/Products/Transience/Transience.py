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
Transient Object Container class.

$Id: Transience.py,v 1.22 2001/11/26 15:29:26 chrism Exp $
"""

__version__='$Revision: 1.22 $'[11:-2]

import Globals
from Globals import HTMLFile
from TransienceInterfaces import ItemWithId,\
     StringKeyedHomogeneousItemContainer, TransientItemContainer
from TransientObject import TransientObject
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from AccessControl import ClassSecurityInfo, getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.User import nobody
from BTrees import OOBTree
from BTrees.Length import Length
from zLOG import LOG, WARNING, BLATHER
import os, math, time, sys, random

DEBUG = os.environ.get('Z_TOC_DEBUG', '')

def DLOG(*args):
    tmp = []
    for arg in args:
        tmp.append(str(arg))
    LOG('Transience DEBUG', BLATHER, ' '.join(tmp))

class MaxTransientObjectsExceeded(Exception): pass

_notfound = []
_marker = []

# permissions
ADD_CONTAINER_PERM = 'Add Transient Object Container'
MGMT_SCREEN_PERM = 'View management screens'
ACCESS_CONTENTS_PERM = 'Access contents information'
CREATE_TRANSIENTS_PERM = 'Create Transient Objects'
ACCESS_TRANSIENTS_PERM = 'Access Transient Objects'
MANAGE_CONTAINER_PERM = 'Manage Transient Object Container'

constructTransientObjectContainerForm = HTMLFile(
    'dtml/addTransientObjectContainer', globals())

def constructTransientObjectContainer(self, id, title='', timeout_mins=20,
    addNotification=None, delNotification=None, limit=0, REQUEST=None):
    """ """
    ob = TransientObjectContainer(
        id, title, timeout_mins, addNotification, delNotification, limit=limit
        )
    self._setObject(id, ob)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class TransientObjectContainer(SimpleItem):
    """ Persists objects for a user-settable time period, after which it
    expires them """
    meta_type = "Transient Object Container"
    icon = "misc_/Transience/datacontainer.gif"
    __implements__ = (ItemWithId,
                      StringKeyedHomogeneousItemContainer,
                      TransientItemContainer
                      )
    manage_options = (
        {   'label': 'Manage',
            'action': 'manage_container',
            'help': ('Transience', 'Transience.stx')
        }, 
        {   'label': 'Security',
            'action': 'manage_access'
        },
    )

    security = ClassSecurityInfo()
    security.setDefaultAccess('deny')

    security.setPermissionDefault(ACCESS_TRANSIENTS_PERM,
                                ['Manager','Anonymous'])
    security.setPermissionDefault(MANAGE_CONTAINER_PERM,['Manager',])
    security.setPermissionDefault(MGMT_SCREEN_PERM,['Manager',])
    security.setPermissionDefault(ACCESS_CONTENTS_PERM,['Manager','Anonymous'])
    security.setPermissionDefault(CREATE_TRANSIENTS_PERM,['Manager',])

    security.declareProtected(MGMT_SCREEN_PERM, 'manage_container')
    manage_container = HTMLFile('dtml/manageTransientObjectContainer',
        globals())

    _limit = 0

    def __init__(self, id, title='', timeout_mins=20, addNotification=None,
        delNotification=None, err_margin=.20, limit=0):
        self.id = id
        self.title=title
        self._addCallback = None
        self._delCallback = None
        self._err_margin = err_margin
        self._setTimeout(timeout_mins)
        self._setLimit(limit)
        self._reset()
        self.setDelNotificationTarget(delNotification)
        self.setAddNotificationTarget(addNotification)

    # -----------------------------------------------------------------
    # ItemWithID
    #

    def getId(self):
        return self.id

    
    # -----------------------------------------------------------------
    # StringKeyedHomogenousItemContainer
    #

    security.declareProtected(CREATE_TRANSIENTS_PERM, 'new_or_existing')
    def new_or_existing(self, k):
        item  = self.get(k, _notfound)
        if item is _notfound: return self.new(k)
        else: return item

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'get')
    def get(self, k, default=_marker):
        # Intentionally uses a different marker than _notfound
        try:
            v = self[k]
        except KeyError:
            if default is _marker: return None
            else: return default
        else:
            if hasattr(v, 'isValid') and v.isValid():
                return v.__of__(self)
            elif not hasattr(v, 'isValid'):
                return v
            else:
                del self[k] # item is no longer valid, so we delete it
                if default is _marker: return None
                else: return default
        
    security.declareProtected(CREATE_TRANSIENTS_PERM, 'new')
    def new(self, k):
        if type(k) is not type(''):
            raise TypeError, (k, "key is not a string type")
        if self.get(k, None) is not None:
            raise KeyError, "duplicate key %s" % k # Not allowed to dup keys
        item = TransientObject(k)
        self[k] = item
        self.notifyAdd(item)
        return item.__of__(self)

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'has_key')
    def has_key(self, k):
        v = self.get(k, _notfound) 
        if v is _notfound: return 0
        return 1

    # -----------------------------------------------------------------
    # TransientItemContainer 
    #

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

    security.declareProtected(MANAGE_CONTAINER_PERM, 'setSubobjectLimit')
    def setSubobjectLimit(self, limit):
        """ """
        if limit != self.getSubobjectLimit():
            self._setLimit(limit)

    security.declareProtected(MGMT_SCREEN_PERM, 'getSubobjectLimit')
    def getSubobjectLimit(self):
        """ """
        return self._limit

    security.declareProtected(MGMT_SCREEN_PERM, 'getAddNotificationTarget')
    def getAddNotificationTarget(self):
        return self._addCallback or ''

    security.declareProtected(MANAGE_CONTAINER_PERM,'setAddNotificationTarget')
    def setAddNotificationTarget(self, f):
        self._addCallback = f             

    security.declareProtected(MGMT_SCREEN_PERM, 'getDelNotificationTarget')
    def getDelNotificationTarget(self):
        return self._delCallback or ''

    security.declareProtected(MANAGE_CONTAINER_PERM,
        'setDelNotificationTarget')
    def setDelNotificationTarget(self, f):
        self._delCallback = f

    # ----------------------------------------------
    # Supporting methods (not part of the interface)
    #

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
                        LOG('Transience', WARNING,
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

    # -----------------------------------------------------------------
    # Management item support (non API)
    #

    security.declareProtected(MANAGE_CONTAINER_PERM,
        'manage_changeTransientObjectContainer')
    def manage_changeTransientObjectContainer(self, title='',
        timeout_mins=20, addNotification=None, delNotification=None,
        limit=0, REQUEST=None):
        """
        Change an existing transient object container.
        """
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
            return self.manage_container(self, REQUEST)

    def _setTimeout(self, timeout_mins):
        if type(timeout_mins) is not type(1):
            raise TypeError, (timeout_mins, "Must be integer")
        self._timeout_secs = timeout_mins * 60

    def _setLimit(self, limit):
        if type(limit) is not type(1):
            raise TypeError, (limit, "Must be integer")
        self._limit = limit

    def _setLastAccessed(self, transientObject):
        sla = getattr(transientObject, 'setLastAccessed', None)
        if sla is not None: sla()

    def _reset(self):
        if hasattr(self,'_ring'):
            for k in self.keys():
                try: self.notifyDestruct(self[k])
                except KeyError: pass
        t_secs = self._timeout_secs
        r_secs = self._resolution_secs = int(t_secs * self._err_margin) or 1
        numbuckets = int(math.floor(t_secs/r_secs)) or 1
        l = []
        i = 0
        now = int(time.time())
        for x in range(numbuckets):
            dump_after = now + i
            c = OOBTree.OOBTree()
            l.insert(0, [c, dump_after])
            i = i + r_secs
        index = OOBTree.OOBTree()
        self._ring = Ring(l, index)
        try: self.__len__.set(0)
        except AttributeError: self.__len__ = self.getLen = Length()

    def _getCurrentBucket(self):
        # no timeout always returns last bucket
        if not self._timeout_secs:
            DEBUG and DLOG('no timeout, returning first bucket')
            b, dump_after = self._ring._data[0]
            return b
        index = self._ring._index
        now = int(time.time())
        i = self._timeout_secs
        # expire all buckets in the ring which have a dump_after time that
        # is before now, turning the ring as many turns as necessary to
        # get to a non-expirable bucket.
        to_clean = []
        while 1:
            l = b, dump_after = self._ring._data[-1]
            if now > dump_after:
                DEBUG and DLOG('dumping... now is %s' % now)
                DEBUG and DLOG('dump_after for %s was %s'%(b, dump_after))
                self._ring.turn()
                # mutate elements in-place in the ring
                new_dump_after = now + i
                l[1] = new_dump_after
                if b: to_clean.append(b)# only clean non-empty buckets
                i = i + self._resolution_secs
            else:
                break
        if to_clean: self._clean(to_clean, index)
        b, dump_after = self._ring._data[0]
        return b

    def _clean(self, bucket_set, index):
        # Build a reverse index.  Eventually, I'll keep this in another
        # persistent struct but I'm afraid of creating more conflicts right
        # now. The reverse index is a mapping from bucketref -> OOSet of string
        # keys.
        rindex = {}
        for k, v in list(index.items()):
            # listifying above is dumb, but I think there's a btrees bug
            # that causes plain old index.items to always return a sequence
            # of even numbers
            if rindex.get(v, _marker) is _marker: rindex[v]=OOBTree.OOSet([k])
            else: rindex[v].insert(k)

        if DEBUG: DLOG("rindex", rindex)

        trans_obs = [] # sequence of objects that we will eventually finalize

        for bucket_to_expire in bucket_set:
            keys = rindex.get(bucket_to_expire, [])
            if keys and DEBUG: DLOG("deleting") 
            for k in keys:
                if DEBUG: DLOG(k)
                trans_obs.append(bucket_to_expire[k])
                del index[k]
                try: self.__len__.change(-1)
                except AttributeError: pass
            bucket_to_expire.clear()
            
        # finalize em
        self.notifyDestruct(trans_obs)

    security.declareProtected(MGMT_SCREEN_PERM, 'nudge')
    def nudge(self):
        """ Used by mgmt interface to turn the bucket set each time
        a screen is shown """
        self._getCurrentBucket()

    def __setitem__(self, k, v):
        current = self._getCurrentBucket()
        index = self._ring._index
        b = index.get(k)
        if b is None:
            # this is a new key
            index[k] = current
            li = self._limit
            # do OOM protection
            if li and len(self) >= li:
                LOG('Transience', WARNING,
                    ('Transient object container %s max subobjects '
                     'reached' % self.id)
                    )
                raise MaxTransientObjectsExceeded, (
                 "%s exceeds maximum number of subobjects %s" % (len(self), li)
                    )
            # do length accounting
            try: self.__len__.change(1)
            except AttributeError: pass 
        elif b is not current:
            # this is an old key that isn't in the current bucket.
            del b[k] # delete it from the old bucket
            index[k] = current
        # change the value
        current[k] = v
        self._setLastAccessed(v)
        
    def __getitem__(self, k):
        current = self._getCurrentBucket()
        index = self._ring._index
        # the next line will raise the proper error if the item has expired
        b = index[k]
        v = b[k] # grab the value before we potentially time it out.
        if b is not current:
            # it's not optimal to do writes in getitem, but there's no choice.
            # we accessed the object, so it should become current.
            index[k] = current # change the index to the current bucket.
            current[k] = v # add the value to the current bucket.
            self._setLastAccessed(v)
            del b[k] # delete the item from the old bucket.
        return v

    def __delitem__(self, k):
        self._getCurrentBucket()
        index = self._ring._index
        b = index[k]
        del index[k]
        del b[k]

    security.declareProtected(ACCESS_TRANSIENTS_PERM, '__len__')
    def __len__(self):
        """ this won't be called unless we havent run __init__ """
        if DEBUG: DLOG('Class __len__ called!')
        self._getCurrentBucket()
        return len(self._ring._index)

    security.declareProtected(ACCESS_TRANSIENTS_PERM, 'getLen')
    getLen = __len__

    def values(self):
        return map(lambda k, self=self: self[k], self.keys())

    def items(self):
        return map(lambda k, self=self: (k, self[k]), self.keys())

    def keys(self):
        self._getCurrentBucket()
        return list(self._ring._index.keys())

class Ring(Persistent):
    """ ring of buckets """
    def __init__(self, l, index):
        if not len(l):
            raise "ring must have at least one element"
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

    # this should really have a _p_resolveConflict, but
    # I've not had time to come up with a reasonable one that
    # works in every circumstance.

Globals.InitializeClass(TransientObjectContainer)

