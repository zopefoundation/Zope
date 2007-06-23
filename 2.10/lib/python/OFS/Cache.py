##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
"""
import time, sys
from logging import getLogger
import Globals
from Globals import InitializeClass
from Globals import DTMLFile
from Acquisition import aq_get, aq_acquire, aq_inner, aq_parent, aq_base

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.Role import _isBeingUsedAsAMethod
from AccessControl import Unauthorized
from AccessControl.Permissions import view_management_screens

ZCM_MANAGERS = '__ZCacheManager_ids__'

ViewManagementScreensPermission = view_management_screens
ChangeCacheSettingsPermission = 'Change cache settings'
LOG = getLogger('Cache')


def isCacheable(ob):
    return getattr(aq_base(ob), '_isCacheable', 0)

def managersExist(ob):
    # Returns 1 if any CacheManagers exist in the context of ob.
    if aq_get(ob, ZCM_MANAGERS, None, 1):
        return 1
    return 0

def filterCacheTab(ob):
    if _isBeingUsedAsAMethod(ob):
        # Show tab when in a ZClass def that uses Cacheable as a base.
        parent = aq_parent(aq_inner(ob))
        return isCacheable(parent)
    else:
        return managersExist(ob)

def filterCacheManagers(orig, container, name, value, extra):
    '''
    This is a filter method for aq_acquire.
    It causes objects to be found only if they are
    in the list of cache managers.
    '''
    if (hasattr(aq_base(container), ZCM_MANAGERS) and
        name in getattr(container, ZCM_MANAGERS)):
        return 1
    return 0

def getVerifiedManagerIds(container):
    '''
    Gets the list of cache managers in a container, verifying each one.
    '''
    ids = getattr(container, ZCM_MANAGERS, ())
    rval = []
    for id in ids:
        if getattr(getattr(container, id, None), '_isCacheManager', 0):
            rval.append(id)
    return tuple(rval)


# Anytime a CacheManager is added or removed, all _v_ZCacheable_cache
# attributes must be invalidated.  manager_timestamp is a way to do
# that.
manager_timestamp = 0


class Cacheable:
    '''Mix-in for cacheable objects.
    '''

    manage_options = ({
        'label':'Cache',
        'action':'ZCacheable_manage',
        'filter':filterCacheTab,
        'help':('OFSP','Cacheable-properties.stx'),
        },)

    security = ClassSecurityInfo()
    security.setPermissionDefault(ChangeCacheSettingsPermission, ('Manager',))

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_manage')
    ZCacheable_manage = DTMLFile('dtml/cacheable', globals())

    _v_ZCacheable_cache = None
    _v_ZCacheable_manager_timestamp = 0
    __manager_id = None
    __enabled = 1
    _isCacheable = 1

    security.declarePrivate('ZCacheable_getManager')
    def ZCacheable_getManager(self):
        '''Returns the currently associated cache manager.'''
        manager_id = self.__manager_id
        if manager_id is None:
            return None
        try:
            return aq_acquire(
                self, manager_id, containment=1,
                filter=filterCacheManagers, extra=None, default=None)
        except AttributeError:
            return None

    security.declarePrivate('ZCacheable_getCache')
    def ZCacheable_getCache(self):
        '''Gets the cache associated with this object.
        '''
        if self.__manager_id is None:
            return None
        c = self._v_ZCacheable_cache
        if c is not None:
            # We have a volatile reference to the cache.
            if self._v_ZCacheable_manager_timestamp == manager_timestamp:
                return aq_base(c)
        manager = self.ZCacheable_getManager()
        if manager is not None:
            c = aq_base(manager.ZCacheManager_getCache())
        else:
            return None
        # Set a volatile reference to the cache then return it.
        self._v_ZCacheable_cache = c
        self._v_ZCacheable_manager_timestamp = manager_timestamp
        return c

    security.declarePrivate('ZCacheable_isCachingEnabled')
    def ZCacheable_isCachingEnabled(self):
        '''
        Returns true only if associated with a cache manager and
        caching of this method is enabled.
        '''
        return self.__enabled and self.ZCacheable_getCache()

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_isAMethod')
    def ZCacheable_isAMethod(self):
        '''
        Returns 1 when this object is a ZClass method.
        '''
        m = _isBeingUsedAsAMethod(self)
        return m

    security.declarePrivate('ZCacheable_getObAndView')
    def ZCacheable_getObAndView(self, view_name):
        """
        If this object is a method of a ZClass and we're working
        with the primary view, uses the ZClass instance as ob
        and our own ID as the view_name.  Otherwise returns
        self and view_name unchanged.
        """
        ob = self
        if not view_name and self.ZCacheable_isAMethod():
            # This is a ZClass method.
            ob = aq_parent(aq_inner(self))
            if isCacheable(ob):
                view_name = self.getId()
            else:
                # Both the parent and the child have to be
                # cacheable.
                ob = self
        return ob, view_name

    security.declarePrivate('ZCacheable_get')
    def ZCacheable_get(self, view_name='', keywords=None,
                       mtime_func=None, default=None):
        '''Retrieves the cached view for the object under the
        conditions specified by keywords. If the value is
        not yet cached, returns the default.
        '''
        c = self.ZCacheable_getCache()
        if c is not None and self.__enabled:
            ob, view_name = self.ZCacheable_getObAndView(view_name)
            try:
                val = c.ZCache_get(ob, view_name, keywords,
                                   mtime_func, default)
                return val
            except:
                LOG.warn('ZCache_get() exception',
                    exc_info=sys.exc_info())
                return default
        return default

    security.declarePrivate('ZCacheable_set')
    def ZCacheable_set(self, data, view_name='', keywords=None,
                       mtime_func=None):
        '''Cacheable views should call this method after generating
        cacheable results. The data argument can be of any Python type.
        '''
        c = self.ZCacheable_getCache()
        if c is not None and self.__enabled:
            ob, view_name = self.ZCacheable_getObAndView(view_name)
            try:
                c.ZCache_set(ob, data, view_name, keywords,
                             mtime_func)
            except:
                LOG.warn('ZCache_set() exception',
                    exc_info=sys.exc_info())

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_invalidate')
    def ZCacheable_invalidate(self, view_name='', REQUEST=None):
        '''Called after a cacheable object is edited. Causes all
        cache entries that apply to the view_name to be removed.
        Returns a status message.
        '''
        c = self.ZCacheable_getCache()
        if c is not None:
            ob, view_name = self.ZCacheable_getObAndView(view_name)
            try:
                message = c.ZCache_invalidate(ob)
                if not message:
                    message = 'Invalidated.'
            except:
                exc = sys.exc_info()
                try:
                    LOG.warn('ZCache_invalidate() exception',
                        exc_info=exc)
                    message = 'An exception occurred: %s: %s' % exc[:2]
                finally:
                    exc = None
        else:
            message = 'This object is not associated with a cache manager.'
        if REQUEST is not None:
            return self.ZCacheable_manage(
                self, REQUEST, management_view='Cache',
                manage_tabs_message=message)
        else:
            return message

    security.declarePrivate('ZCacheable_getModTime')
    def ZCacheable_getModTime(self, mtime_func=None):
        '''Returns the highest of the last mod times.'''
        # Based on:
        #   mtime_func
        #   self.mtime
        #   self.__class__.mtime
        #   (if in a ZClass) zclass_instance.mtime
        #                    zclass_instance.__class__.mtime
        mtime = 0
        if mtime_func:
            # Allow mtime_func to influence the mod time.
            mtime = mtime_func()
        base = aq_base(self)
        mtime = max(getattr(base, '_p_mtime', mtime), mtime)
        klass = getattr(base, '__class__', None)
        if klass:
            mtime = max(getattr(klass, '_p_mtime', mtime), mtime)
        if self.ZCacheable_isAMethod():
            # This is a ZClass method.
            instance = aq_parent(aq_inner(self))
            base = aq_base(instance)
            mtime = max(getattr(base, '_p_mtime', mtime), mtime)
            klass = getattr(base, '__class__', None)
            if klass:
                mtime = max(getattr(klass, '_p_mtime', mtime), mtime)
        return mtime

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_getManagerId')
    def ZCacheable_getManagerId(self):
        '''Returns the id of the current ZCacheManager.'''
        return self.__manager_id

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_getManagerURL')
    def ZCacheable_getManagerURL(self):
        '''Returns the URL of the current ZCacheManager.'''
        manager = self.ZCacheable_getManager()
        if manager is not None:
            return manager.absolute_url()
        return None

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_getManagerIds')
    def ZCacheable_getManagerIds(self):
        '''Returns a list of mappings containing the id and title
        of the available ZCacheManagers.'''
        rval = []
        ob = self
        used_ids = {}
        while ob is not None:
            if hasattr(aq_base(ob), ZCM_MANAGERS):
                ids = getattr(ob, ZCM_MANAGERS)
                for id in ids:
                    manager = getattr(ob, id, None)
                    if manager is not None:
                        id = manager.getId()
                        if not used_ids.has_key(id):
                            title = getattr(aq_base(manager),
                                            'title', '')
                            rval.append({'id':id, 'title':title})
                            used_ids[id] = 1
            ob = aq_parent(aq_inner(ob))
        return tuple(rval)

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheable_setManagerId')
    def ZCacheable_setManagerId(self, manager_id, REQUEST=None):
        '''Changes the manager_id for this object.'''
        self.ZCacheable_invalidate()
        if not manager_id:
            # User requested disassociation
            # from the cache manager.
            manager_id = None
        else:
            manager_id = str(manager_id)
        self.__manager_id = manager_id
        self._v_ZCacheable_cache = None
        if REQUEST is not None:
            return self.ZCacheable_manage(
                self, REQUEST, management_view='Cache',
                manage_tabs_message='Cache settings changed.')

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_enabled')
    def ZCacheable_enabled(self):
        '''Returns true if caching is enabled for this object
        or method.'''
        return self.__enabled

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheable_setEnabled')
    def ZCacheable_setEnabled(self, enabled=0, REQUEST=None):
        '''Changes the enabled flag. Normally used only when
        setting up cacheable ZClass methods.'''
        self.__enabled = enabled and 1 or 0
        if REQUEST is not None:
            return self.ZCacheable_manage(
                self, REQUEST, management_view='Cache',
                manage_tabs_message='Cache settings changed.')

    security.declareProtected(ViewManagementScreensPermission,
                              'ZCacheable_configHTML')
    def ZCacheable_configHTML(self):
        '''Override to provide configuration of caching
        behavior that can only be specific to the cacheable object.
        '''
        return ''


InitializeClass(Cacheable)


def findCacheables(ob, manager_id, require_assoc, subfolders,
                   meta_types, rval, path):
    '''
    Used by the CacheManager UI.  Recursive.  Similar to the Zope
    "Find" function.  Finds all Cacheable objects in a hierarchy.
    '''
    try:
        if meta_types:
            subobs = ob.objectValues(meta_types)
        else:
            subobs = ob.objectValues()
        sm = getSecurityManager()

        # Add to the list of cacheable objects.
        for subob in subobs:
            if not isCacheable(subob):
                continue
            associated = (subob.ZCacheable_getManagerId() == manager_id)
            if require_assoc and not associated:
                continue
            if not sm.checkPermission('Change cache settings', subob):
                continue
            subpath = path + (subob.getId(),)
            icon = getattr(aq_base(subob), 'icon', '')
            info = {
                'sortkey': subpath,
                'path': '/'.join(subpath),
                'title': getattr(aq_base(subob), 'title', ''),
                'icon': icon,
                'associated': associated,}
            rval.append(info)

        # Visit subfolders.
        if subfolders:
            if meta_types:
                subobs = ob.objectValues()
            for subob in subobs:
                subpath = path + (subob.getId(),)
                if hasattr(aq_base(subob), 'objectValues'):
                    if sm.checkPermission(
                        'Access contents information', subob):
                        findCacheables(
                            subob, manager_id, require_assoc,
                            subfolders, meta_types, rval, subpath)
    except:
        # Ignore exceptions.
        import traceback
        traceback.print_exc()


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

    manage_options = (
        {'label':'Associate',
         'action':'ZCacheManager_associate',
         'help':('OFSP','CacheManager-associate.stx'),
         },
        )

    def manage_afterAdd(self, item, container):
        # Adds self to the list of cache managers in the container.
        if aq_base(self) is aq_base(item):
            ids = getVerifiedManagerIds(container)
            id = self.getId()
            if id not in ids:
                setattr(container, ZCM_MANAGERS, ids + (id,))
                global manager_timestamp
                manager_timestamp = time.time()

    def manage_beforeDelete(self, item, container):
        # Removes self from the list of cache managers.
        if aq_base(self) is aq_base(item):
            ids = getVerifiedManagerIds(container)
            id = self.getId()
            if id in ids:
                setattr(container, ZCM_MANAGERS, filter(
                    lambda s, id=id: s != id, ids))
                global manager_timestamp
                manager_timestamp = time.time()

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheManager_associate')
    ZCacheManager_associate = DTMLFile('dtml/cmassoc', globals())

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheManager_locate')
    def ZCacheManager_locate(self, require_assoc, subfolders,
                             meta_types=[], REQUEST=None):
        '''Locates cacheable objects.
        '''
        ob = aq_parent(aq_inner(self))
        rval = []
        manager_id = self.getId()
        if '' in meta_types:
            # User selected "All".
            meta_types = []
        findCacheables(ob, manager_id, require_assoc, subfolders,
                       meta_types, rval, ())
        if REQUEST is not None:
            return self.ZCacheManager_associate(
                self, REQUEST, show_results=1, results=rval,
                management_view="Associate")
        else:
            return rval

    security.declareProtected(ChangeCacheSettingsPermission,
                              'ZCacheManager_setAssociations')
    def ZCacheManager_setAssociations(self, props=None, REQUEST=None):
        '''Associates and un-associates cacheable objects with this
        cache manager.
        '''
        addcount = 0
        remcount = 0
        parent = aq_parent(aq_inner(self))
        sm = getSecurityManager()
        my_id = str(self.getId())
        if props is None:
            props = REQUEST.form
        for key, do_associate in props.items():
            if key[:10] == 'associate_':
                path = key[10:]
                ob = parent.restrictedTraverse(path)
                if not sm.checkPermission('Change cache settings', ob):
                    raise Unauthorized
                if not isCacheable(ob):
                    # Not a cacheable object.
                    continue
                manager_id = str(ob.ZCacheable_getManagerId())
                if do_associate:
                    if manager_id != my_id:
                        ob.ZCacheable_setManagerId(my_id)
                        addcount = addcount + 1
                else:
                    if manager_id == my_id:
                        ob.ZCacheable_setManagerId(None)
                        remcount = remcount + 1
        if REQUEST is not None:
            return self.ZCacheManager_associate(
                self, REQUEST, management_view="Associate",
                manage_tabs_message='%d association(s) made, %d removed.'%
                (addcount, remcount)
                )

InitializeClass(CacheManager)
