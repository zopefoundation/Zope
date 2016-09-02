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
"""Cacheable object and cache management base classes.
"""

from logging import getLogger

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo

ZCM_MANAGERS = '__ZCacheManager_ids__'

ViewManagementScreensPermission = view_management_screens
ChangeCacheSettingsPermission = 'Change cache settings'
LOG = getLogger('Cache')


def isCacheable(ob):
    return False


def managersExist(ob):
    # Returns 1 if any CacheManagers exist in the context of ob.
    return False


def filterCacheTab(ob):
    return False


def filterCacheManagers(orig, container, name, value, extra):
    '''
    This is a filter method for aq_acquire.
    It causes objects to be found only if they are
    in the list of cache managers.
    '''
    return False


def getVerifiedManagerIds(container):
    '''
    Gets the list of cache managers in a container, verifying each one.
    '''
    return ()


# Anytime a CacheManager is added or removed, all _v_ZCacheable_cache
# attributes must be invalidated.  manager_timestamp is a way to do
# that.
manager_timestamp = 0


class Cacheable(object):
    '''Mix-in for cacheable objects.
    '''

    manage_options = ()

    security = ClassSecurityInfo()
    security.setPermissionDefault(ChangeCacheSettingsPermission, ('Manager',))

    _v_ZCacheable_cache = None
    _v_ZCacheable_manager_timestamp = 0
    __manager_id = None
    __enabled = False
    _isCacheable = False

    security.declarePrivate('ZCacheable_getManager')
    def ZCacheable_getManager(self):
        '''Returns the currently associated cache manager.'''
        return None

    security.declarePrivate('ZCacheable_getCache')
    def ZCacheable_getCache(self):
        '''Gets the cache associated with this object.
        '''
        return None

    security.declarePrivate('ZCacheable_isCachingEnabled')
    def ZCacheable_isCachingEnabled(self):
        '''
        Returns true only if associated with a cache manager and
        caching of this method is enabled.
        '''
        return False

    security.declarePrivate('ZCacheable_getObAndView')
    def ZCacheable_getObAndView(self, view_name):
        # Returns self and view_name unchanged.
        return self, view_name

    security.declarePrivate('ZCacheable_get')
    def ZCacheable_get(self, view_name='', keywords=None,
                       mtime_func=None, default=None):
        '''Retrieves the cached view for the object under the
        conditions specified by keywords. If the value is
        not yet cached, returns the default.
        '''
        return default

    security.declarePrivate('ZCacheable_set')
    def ZCacheable_set(self, data, view_name='', keywords=None,
                       mtime_func=None):
        '''Cacheable views should call this method after generating
        cacheable results. The data argument can be of any Python type.
        '''
        pass

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_invalidate')
    def ZCacheable_invalidate(self, view_name='', REQUEST=None):
        '''Called after a cacheable object is edited. Causes all
        cache entries that apply to the view_name to be removed.
        Returns a status message.
        '''
        pass

    security.declarePrivate('ZCacheable_getModTime')
    def ZCacheable_getModTime(self, mtime_func=None):
        '''Returns the highest of the last mod times.'''
        return 0

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_getManagerId')
    def ZCacheable_getManagerId(self):
        '''Returns the id of the current ZCacheManager.'''
        return None

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_getManagerURL')
    def ZCacheable_getManagerURL(self):
        '''Returns the URL of the current ZCacheManager.'''
        return None

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_getManagerIds')
    def ZCacheable_getManagerIds(self):
        '''Returns a list of mappings containing the id and title
        of the available ZCacheManagers.'''
        return ()

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheable_setManagerId')
    def ZCacheable_setManagerId(self, manager_id, REQUEST=None):
        '''Changes the manager_id for this object.'''
        pass

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_enabled')
    def ZCacheable_enabled(self):
        '''Returns true if caching is enabled for this object
        or method.'''
        return False

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheable_setEnabled')
    def ZCacheable_setEnabled(self, enabled=0, REQUEST=None):
        '''Changes the enabled flag.'''
        pass


InitializeClass(Cacheable)


class Cache:
    '''
    A base class (and interface description) for caches.
    Note that Cache objects are not intended to be visible by
    restricted code.
    '''

    def ZCache_invalidate(self, ob):
        raise NotImplementedError

    def ZCache_get(self, ob, view_name, keywords, mtime_func, default):
        # view_name: If an object provides different views that would
        #   benefit from caching, it will set view_name.
        #   Otherwise view_name will be an empty string.
        #
        # keywords: Either None or a mapping containing keys that
        #   distinguish this cache entry from others even though
        #   ob and view_name are the same.  DTMLMethods use keywords
        #   derived from the DTML namespace.
        #
        # mtime_func: When the Cache calls ZCacheable_getModTime(),
        #   it should pass this as an argument.  It is provided to
        #   allow cacheable objects to provide their own computation
        #   of the object's modification time.
        #
        # default: If no entry is found, ZCache_get() should return
        #   default.
        raise NotImplementedError

    def ZCache_set(self, ob, data, view_name, keywords, mtime_func):
        # See ZCache_get() for parameter descriptions.
        raise NotImplementedError


class CacheManager:
    '''
    A base class for cache managers.  Implement ZCacheManager_getCache().
    '''

    security = ClassSecurityInfo()
    security.setPermissionDefault(ChangeCacheSettingsPermission, ('Manager',))

    security.declarePrivate('ZCacheManager_getCache')
    def ZCacheManager_getCache(self):
        raise NotImplementedError

    _isCacheManager = 1

    manage_options = ()

    def manage_afterAdd(self, item, container):
        # Adds self to the list of cache managers in the container.
        pass

    def manage_beforeDelete(self, item, container):
        # Removes self from the list of cache managers.
        pass

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheManager_locate')
    def ZCacheManager_locate(self, require_assoc, subfolders,
                             meta_types=[], REQUEST=None):
        '''Locates cacheable objects.
        '''
        return []

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheManager_setAssociations')
    def ZCacheManager_setAssociations(self, props=None, REQUEST=None):
        '''Associates and un-associates cacheable objects with this
        cache manager.
        '''
        pass

InitializeClass(CacheManager)
