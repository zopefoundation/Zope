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
'''
RAM cache manager --
  Caches the results of method calls in RAM.

$Id$
'''


from OFS.Cache import Cache, CacheManager
from OFS.SimpleItem import SimpleItem
from thread import allocate_lock
import time
import Globals
from Globals import DTMLFile
from string import join, split

try: from cPickle import Pickler
except: from pickle import Pickler

try: from cStringIO import dumps
except: from pickle import dumps

_marker = []  # Create a new marker object.


class CacheException (Exception):
    '''
    A cache-related exception.
    '''


class CacheEntry:
    '''
    Represents a cached value.
    '''

    def __init__(self, index, data, view_name):
        try:
            # This is a protective barrier that hopefully prevents
            # us from caching something that might result in memory
            # leaks.  It's also convenient for determining the
            # approximate memory usage of the cache entry.
            self.size = len(dumps(index)) + len(dumps(data))
        except:
            raise CacheException('The data for the cache is not pickleable.')
        self.created = time.time()
        self.data = data
        self.view_name = view_name
        self.access_count = 0


class ObjectCacheEntries:
    '''
    Represents the cache for one Zope object.
    '''

    hits = 0
    misses = 0

    def __init__(self, path):
        self.physical_path = path
        self.lastmod = 0  # Mod time of the object, class, etc.
        self.entries = {}

    def aggregateIndex(self, view_name, req, req_names, local_keys):
        '''
        Returns the index to be used when looking for or inserting
        a cache entry.
        view_name is a string.
        local_keys is a mapping or None.
        '''
        req_index = []
        # Note: req_names is already sorted.
        for key in req_names:
            if req is None:
                val = ''
            else:
                val = req.get(key, '')
            req_index.append((str(key), str(val)))
        if local_keys:
            local_index = []
            for key, val in local_keys.items():
                local_index.append((str(key), str(val)))
            local_index.sort()
        else:
            local_index = ()
        return (str(view_name), tuple(req_index), tuple(local_index))

    def getEntry(self, lastmod, index):
        if self.lastmod < lastmod:
            # Expired.
            self.entries = {}
            self.lastmod = lastmod
            return _marker
        return self.entries.get(index, _marker)

    def setEntry(self, lastmod, index, data, view_name):
        self.lastmod = lastmod
        self.entries[index] = CacheEntry(index, data, view_name)

    def delEntry(self, index):
        try: del self.entries[index]
        except KeyError: pass


class RAMCache (Cache):
    # Note the need to take thread safety into account.
    # Also note that objects of this class are not persistent,
    # nor do they make use of acquisition.
    max_age = 0

    def __init__(self):
        # cache maps physical paths to ObjectCacheEntries.
        self.cache = {}
        self.writelock = allocate_lock()
        self.next_cleanup = 0

    def initSettings(self, kw):
        # Note that we lazily allow RAMCacheManager
        # to verify the correctness of the internal settings.
        self.__dict__.update(kw)

    def getObjectCacheEntries(self, ob, create=0):
        """
        Finds or creates the associated ObjectCacheEntries object.
        Remember to lock writelock when calling with the 'create' flag.
        """
        cache = self.cache
        path = ob.getPhysicalPath()
        oc = cache.get(path, None)
        if oc is None:
            if create:
                cache[path] = oc = ObjectCacheEntries(path)
            else:
                return None
        return oc
        
    def countAllEntries(self):
        '''
        Returns the count of all cache entries.
        '''
        count = 0
        for oc in self.cache.values():
            count = count + len(oc.entries)
        return count

    def countAccesses(self):
        '''
        Returns a mapping of
        (n) -> number of entries accessed (n) times
        '''
        counters = {}
        for oc in self.cache.values():
            for entry in oc.entries.values():
                access_count = entry.access_count
                counters[access_count] = counters.get(
                    access_count, 0) + 1
        return counters

    def clearAccessCounters(self):
        '''
        Clears access_count for each cache entry.
        '''
        for oc in self.cache.values():
            for entry in oc.entries.values():
                entry.access_count = 0

    def deleteEntriesAtOrBelowThreshold(self, threshold_access_count):
        """
        Deletes entries that haven't been accessed recently.
        """
        self.writelock.acquire()
        try:
            for p, oc in self.cache.items():
                for agindex, entry in oc.entries.items():
                    if entry.access_count <= threshold_access_count:
                        del oc.entries[agindex]
                if len(oc.entries) < 1:
                    del self.cache[p]
        finally:
            self.writelock.release()

    def deleteStaleEntries(self):
        """
        Deletes entries that have expired.
        """
        if self.max_age > 0:
            self.writelock.acquire()
            try:
                min_created = time.time() - self.max_age
                for p, oc in self.cache.items():
                    for agindex, entry in oc.entries.items():
                        if entry.created < min_created:
                            del oc.entries[agindex]
                    if len(oc.entries) < 1:
                        del self.cache[p]
            finally:
                self.writelock.release()

    def cleanup(self):
        '''
        Removes cache entries.
        '''
        self.deleteStaleEntries()
        new_count = self.countAllEntries()
        if new_count > self.threshold:
            counters = self.countAccesses()
            priorities = counters.items()
            # Remove the least accessed entries until we've reached
            # our target count.
            if len(priorities) > 0:
                priorities.sort()
                access_count = 0
                for access_count, effect in priorities:
                    new_count = new_count - effect
                    if new_count <= self.threshold:
                        break
                self.deleteEntriesAtOrBelowThreshold(access_count)
                self.clearAccessCounters()

    def getCacheReport(self):
        """
        Reports on the contents of the cache.
        """
        rval = []
        for oc in self.cache.values():
            size = 0
            ac = 0
            views = []
            for entry in oc.entries.values():
                size = size + entry.size
                ac = ac + entry.access_count
                view = entry.view_name or '<default>'
                if view not in views:
                    views.append(view)
            views.sort()
            info = {'path': join(oc.physical_path, '/'),
                    'hits': oc.hits,
                    'misses': oc.misses,
                    'size': size,
                    'counter': ac,
                    'views': views,
                    'entries': len(oc.entries)
                    }
            rval.append(info)
        return rval

    def ZCache_invalidate(self, ob):
        '''
        Invalidates the cache entries that apply to ob.
        '''
        path = ob.getPhysicalPath()
        # Invalidates all subobjects as well.
        self.writelock.acquire()
        try:
            for p, oc in self.cache.items():
                pp = oc.physical_path
                if pp[:len(path)] == path:
                    del self.cache[p]
        finally:
            self.writelock.release()

    def ZCache_get(self, ob, view_name='', keywords=None,
                   mtime_func=None, default=None):
        '''
        Gets a cache entry or returns default.
        '''
        oc = self.getObjectCacheEntries(ob)
        if oc is None:
            return default
        lastmod = ob.ZCacheable_getModTime(mtime_func)
        index = oc.aggregateIndex(view_name, ob.REQUEST,
                                  self.request_vars, keywords)
        entry = oc.getEntry(lastmod, index)
        if entry is _marker:
            return default
        if self.max_age > 0 and entry.created < time.time() - self.max_age:
            # Expired.
            self.writelock.acquire()
            try:
                oc.delEntry(index)
            finally:
                self.writelock.release()
            return default
        oc.hits = oc.hits + 1
        entry.access_count = entry.access_count + 1
        return entry.data
        
    def ZCache_set(self, ob, data, view_name='', keywords=None,
                   mtime_func=None):
        '''
        Sets a cache entry.
        '''
        now = time.time()
        if self.next_cleanup <= now:
            self.cleanup()
            self.next_cleanup = now + self.cleanup_interval

        lastmod = ob.ZCacheable_getModTime(mtime_func)
        self.writelock.acquire()
        try:
            oc = self.getObjectCacheEntries(ob, create=1)
            index = oc.aggregateIndex(view_name, ob.REQUEST,
                                      self.request_vars, keywords)
            oc.setEntry(lastmod, index, data, view_name)
            oc.misses = oc.misses + 1
        finally:
            self.writelock.release()

caches = {}
PRODUCT_DIR = split(__name__, '.')[-2]

class RAMCacheManager (CacheManager, SimpleItem):
    ' '

    __ac_permissions__ = (
        ('View management screens', ('getSettings',
                                     'manage_main',
                                     'manage_stats',
                                     'getCacheReport',
                                     'sort_link',)),
        ('Change cache managers', ('manage_editProps',), ('Manager',)),
        )

    manage_options = (
        {'label':'Properties', 'action':'manage_main',
         'help':(PRODUCT_DIR, 'RAM.stx'),},
        {'label':'Statistics', 'action':'manage_stats',
         'help':(PRODUCT_DIR, 'RAM.stx'),},
        ) + CacheManager.manage_options + SimpleItem.manage_options

    meta_type = 'RAM Cache Manager'

    def __init__(self, ob_id):
        self.id = ob_id
        self.title = ''
        self._settings = {
            'threshold': 1000,
            'cleanup_interval': 300,
            'request_vars': ('AUTHENTICATED_USER',),
            'max_age': 3600,
            }
        self.__cacheid = '%s_%f' % (id(self), time.time())

    def getId(self):
        ' '
        return self.id
        
    ZCacheManager_getCache__roles__ = ()
    def ZCacheManager_getCache(self):
        cacheid = self.__cacheid
        try:
            return caches[cacheid]
        except KeyError:
            cache = RAMCache()
            cache.initSettings(self._settings)
            caches[cacheid] = cache
            return cache

    def getSettings(self):
        'Returns the current cache settings.'
        res = self._settings.copy()
        if not res.has_key('max_age'):
            res['max_age'] = 0
        return res

    manage_main = DTMLFile('dtml/propsRCM', globals())

    def manage_editProps(self, title, settings=None, REQUEST=None):
        'Changes the cache settings.'
        if settings is None:
            settings = REQUEST
        self.title = str(title)
        request_vars = list(settings['request_vars'])
        request_vars.sort()
        self._settings = {
            'threshold': int(settings['threshold']),
            'cleanup_interval': int(settings['cleanup_interval']),
            'request_vars': tuple(request_vars),
            'max_age': int(settings['max_age']),
            }
        cache = self.ZCacheManager_getCache()
        cache.initSettings(self._settings)
        if REQUEST is not None:
            return self.manage_main(
                self, REQUEST, manage_tabs_message='Properties changed.')

    manage_stats = DTMLFile('dtml/statsRCM', globals())

    def _getSortInfo(self):
        """
        Returns the value of sort_by and sort_reverse.
        If not found, returns default values.
        """
        req = self.REQUEST
        sort_by = req.get('sort_by', 'hits')
        sort_reverse = int(req.get('sort_reverse', 1))
        return sort_by, sort_reverse        

    def getCacheReport(self):
        """
        Returns the list of objects in the cache, sorted according to
        the user's preferences.
        """
        sort_by, sort_reverse = self._getSortInfo()
        c = self.ZCacheManager_getCache()
        rval = c.getCacheReport()
        if sort_by:
            rval.sort(lambda e1, e2, sort_by=sort_by:
                      cmp(e1[sort_by], e2[sort_by]))
            if sort_reverse:
                rval.reverse()
        return rval

    def sort_link(self, name, id):
        """
        Utility for generating a sort link.
        """
        sort_by, sort_reverse = self._getSortInfo()
        url = self.absolute_url() + '/manage_stats?sort_by=' + id
        newsr = 0
        if sort_by == id:
            newsr = not sort_reverse
        url = url + '&sort_reverse=' + (newsr and '1' or '0')
        return '<a href="%s">%s</a>' % (url, name)

Globals.default__class_init__(RAMCacheManager)


manage_addRAMCacheManagerForm = DTMLFile('dtml/addRCM', globals())

def manage_addRAMCacheManager(self, id, REQUEST=None):
    'Adds a RAM cache manager to the folder.'
    self._setObject(id, RAMCacheManager(id))
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)
