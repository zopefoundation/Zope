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
'''
RAM cache manager --
  Caches the results of method calls in RAM.

$Id$
'''
from cgi import escape
from thread import allocate_lock
import time

from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.Cache import Cache
from OFS.Cache import CacheManager
from OFS.SimpleItem import SimpleItem

try:
    from cPickle import Pickler
    from cPickle import HIGHEST_PROTOCOL
except ImportError:
    from pickle import Pickler
    from pickle import HIGHEST_PROTOCOL

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
            # DM 2004-11-29: this code causes excessive time.
            #   Note also that it does not prevent us from
            #   caching objects with references to persistent objects
            #   When we do, nasty persistency errors are likely
            #   to occur ("shouldn't load data while connection is closed").
            #self.size = len(dumps(index)) + len(dumps(data))
            sizer = _ByteCounter()
            pickler = Pickler(sizer, HIGHEST_PROTOCOL)
            pickler.dump(index)
            pickler.dump(data)
            self.size = sizer.getCount()
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
            info = {'path': '/'.join(oc.physical_path),
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
PRODUCT_DIR = __name__.split('.')[-2]

class RAMCacheManager (CacheManager, SimpleItem):
    """Manage a RAMCache, which stores rendered data in RAM. 

    This is intended to be used as a low-level cache for
    expensive Python code, not for objects published
    under their own URLs such as web pages.

    RAMCacheManager *can* be used to cache complete publishable
    pages, such as DTMLMethods/Documents and Page Templates, 
    but this is not advised: such objects typically do not attempt
    to cache important out-of-band data such as 3xx HTTP responses,
    and the client would get an erroneous 200 response.

    Such objects should instead be cached with an                             
    AcceleratedHTTPCacheManager and/or downstream                               
    caching.
    """

    security = ClassSecurityInfo()
    security.setPermissionDefault('Change cache managers', ('Manager',))

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
        self._resetCacheId()

    def getId(self):
        ' '
        return self.id

    security.declarePrivate('_remove_data')
    def _remove_data(self):
        caches.pop(self.__cacheid, None)

    security.declarePrivate('_resetCacheId')
    def _resetCacheId(self):
        self.__cacheid = '%s_%f' % (id(self), time.time())

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

    security.declareProtected(view_management_screens, 'getSettings')
    def getSettings(self):
        'Returns the current cache settings.'
        res = self._settings.copy()
        if not res.has_key('max_age'):
            res['max_age'] = 0
        return res

    security.declareProtected(view_management_screens, 'manage_main')
    manage_main = DTMLFile('dtml/propsRCM', globals())

    security.declareProtected('Change cache managers', 'manage_editProps')
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

    security.declareProtected(view_management_screens, 'manage_stats')
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

    security.declareProtected(view_management_screens, 'getCacheReport')
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

    security.declareProtected(view_management_screens, 'sort_link')
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
        return '<a href="%s">%s</a>' % (escape(url, 1), escape(name))

    security.declareProtected('Change cache managers', 'manage_invalidate')
    def manage_invalidate(self, paths, REQUEST=None):
        """ ZMI helper to invalidate an entry """
        for path in paths:
            try:
                ob = self.unrestrictedTraverse(path)
            except (AttributeError, KeyError):
                pass

            ob.ZCacheable_invalidate()

        if REQUEST is not None:
            msg = 'Cache entries invalidated'
            return self.manage_stats(manage_tabs_message=msg)

InitializeClass(RAMCacheManager)


class _ByteCounter:
    '''auxiliary file like class which just counts the bytes written.'''
    _count = 0

    def write(self, bytes):
        self._count += len(bytes)

    def getCount(self):
        return self._count

manage_addRAMCacheManagerForm = DTMLFile('dtml/addRCM', globals())

def manage_addRAMCacheManager(self, id, REQUEST=None):
    'Adds a RAM cache manager to the folder.'
    self._setObject(id, RAMCacheManager(id))
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)
