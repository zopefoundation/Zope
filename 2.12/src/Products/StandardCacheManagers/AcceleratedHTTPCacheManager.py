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
Accelerated HTTP cache manager --
  Adds caching headers to the response so that downstream caches will
  cache according to a common policy.

$Id$
'''
from cgi import escape
import httplib
import logging
import socket
import time
from urllib import quote
import urlparse

from AccessControl.Permissions import view_management_screens
from AccessControl.SecurityInfo import ClassSecurityInfo
from App.Common import rfc1123_date
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.Cache import Cache
from OFS.Cache import CacheManager
from OFS.SimpleItem import SimpleItem

logger = logging.getLogger('Zope.AcceleratedHTTPCacheManager')

class AcceleratedHTTPCache (Cache):
    # Note the need to take thread safety into account.
    # Also note that objects of this class are not persistent,
    # nor do they use acquisition.

    connection_factory = httplib.HTTPConnection

    def __init__(self):
        self.hit_counts = {}

    def initSettings(self, kw):
        # Note that we lazily allow AcceleratedHTTPCacheManager
        # to verify the correctness of the internal settings.
        self.__dict__.update(kw)

    def ZCache_invalidate(self, ob):
        # Note that this only works for default views of objects at
        # their canonical path. If an object is viewed and cached at
        # any other path via acquisition or virtual hosting, that
        # cache entry cannot be purged because there is an infinite
        # number of such possible paths, and Squid does not support
        # any kind of fuzzy purging; we have to specify exactly the
        # URL to purge.  So we try to purge the known paths most
        # likely to turn up in practice: the physical path and the
        # current absolute_url_path.  Any of those can be
        # wrong in some circumstances, but it may be the best we can
        # do :-(
        # It would be nice if Squid's purge feature was better
        # documented.  (pot! kettle! black!)

        phys_path = ob.getPhysicalPath()
        if self.hit_counts.has_key(phys_path):
            del self.hit_counts[phys_path]
        purge_paths = (ob.absolute_url_path(), quote('/'.join(phys_path)))
        # Don't purge the same path twice.
        if purge_paths[0] == purge_paths[1]:
            purge_paths  = purge_paths[:1]
        results = []
        for url in self.notify_urls:
            if not url.strip():
                continue
            # Send the PURGE request to each HTTP accelerator.
            if url[:7].lower() == 'http://':
                u = url
            else:
                u = 'http://' + url
            (scheme, host, path, params, query, fragment
             ) = urlparse.urlparse(u)
            if path.lower().startswith('/http://'):
                    path = path.lstrip('/')
            for ob_path in purge_paths:
                p = path.rstrip('/') + ob_path
                h = self.connection_factory(host)
                logger.debug('PURGING host %s, path %s' % (host, p))
                # An exception on one purge should not prevent the others.
                try:
                    h.request('PURGE', p)
                    # This better not hang. I wish httplib gave us
                    # control of timeouts.
                except socket.gaierror:
                    msg = 'socket.gaierror: maybe the server ' + \
                          'at %s is down, or the cache manager ' + \
                          'is misconfigured?'
                    logger.error(msg % url)
                    continue
                r = h.getresponse()
                status = '%s %s' % (r.status, r.reason)
                results.append(status)
                logger.debug('purge response: %s' % status)
        return 'Server response(s): ' + ';'.join(results)

    def ZCache_get(self, ob, view_name, keywords, mtime_func, default):
        return default

    def ZCache_set(self, ob, data, view_name, keywords, mtime_func):
        # Note the blatant ignorance of view_name and keywords.
        # Standard HTTP accelerators are not able to make use of this
        # data.  mtime_func is also ignored because using "now" for
        # Last-Modified is as good as using any time in the past.
        REQUEST = ob.REQUEST
        RESPONSE = REQUEST.RESPONSE
        anon = 1
        u = REQUEST.get('AUTHENTICATED_USER', None)
        if u is not None:
            if u.getUserName() != 'Anonymous User':
                anon = 0
        phys_path = ob.getPhysicalPath()
        if self.hit_counts.has_key(phys_path):
            hits = self.hit_counts[phys_path]
        else:
            self.hit_counts[phys_path] = hits = [0,0]
        if anon:
            hits[0] = hits[0] + 1
        else:
            hits[1] = hits[1] + 1

        if not anon and self.anonymous_only:
            return
        # Set HTTP Expires and Cache-Control headers
        seconds=self.interval
        expires=rfc1123_date(time.time() + seconds)
        RESPONSE.setHeader('Last-Modified',rfc1123_date(time.time()))
        RESPONSE.setHeader('Cache-Control', 'max-age=%d' % seconds)
        RESPONSE.setHeader('Expires', expires)


caches = {}
PRODUCT_DIR = __name__.split('.')[-2]

class AcceleratedHTTPCacheManager (CacheManager, SimpleItem):
    ' '

    security = ClassSecurityInfo()
    security.setPermissionDefault('Change cache managers', ('Manager',))

    manage_options = (
        {'label':'Properties', 'action':'manage_main',
         'help':(PRODUCT_DIR, 'Accel.stx'),},
        {'label':'Statistics', 'action':'manage_stats',
         'help':(PRODUCT_DIR, 'Accel.stx'),},
        ) + CacheManager.manage_options + SimpleItem.manage_options

    meta_type = 'Accelerated HTTP Cache Manager'

    def __init__(self, ob_id):
        self.id = ob_id
        self.title = ''
        self._settings = {'anonymous_only':1,
                          'interval':3600,
                          'notify_urls':()}
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

    security.declarePrivate('ZCacheManager_getCache')
    def ZCacheManager_getCache(self):
        cacheid = self.__cacheid
        try:
            return caches[cacheid]
        except KeyError:
            cache = AcceleratedHTTPCache()
            cache.initSettings(self._settings)
            caches[cacheid] = cache
            return cache

    security.declareProtected(view_management_screens, 'getSettings')
    def getSettings(self):
        ' '
        return self._settings.copy()  # Don't let UI modify it.

    security.declareProtected(view_management_screens, 'manage_main')
    manage_main = DTMLFile('dtml/propsAccel', globals())

    security.declareProtected('Change cache managers', 'manage_editProps')
    def manage_editProps(self, title, settings=None, REQUEST=None):
        ' '
        if settings is None:
            settings = REQUEST
        self.title = str(title)
        self._settings = {
            'anonymous_only':settings.get('anonymous_only') and 1 or 0,
            'interval':int(settings['interval']),
            'notify_urls':tuple(settings['notify_urls']),}
        cache = self.ZCacheManager_getCache()
        cache.initSettings(self._settings)
        if REQUEST is not None:
            return self.manage_main(
                self, REQUEST, manage_tabs_message='Properties changed.')

    security.declareProtected(view_management_screens, 'manage_stats')
    manage_stats = DTMLFile('dtml/statsAccel', globals())

    def _getSortInfo(self):
        """
        Returns the value of sort_by and sort_reverse.
        If not found, returns default values.
        """
        req = self.REQUEST
        sort_by = req.get('sort_by', 'anon')
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
        rval = []
        for path, (anon, auth) in c.hit_counts.items():
            rval.append({'path': '/'.join(path),
                         'anon': anon,
                         'auth': auth})
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
        # XXX This ought to be in a library or something.
        sort_by, sort_reverse = self._getSortInfo()
        url = self.absolute_url() + '/manage_stats?sort_by=' + id
        newsr = 0
        if sort_by == id:
            newsr = not sort_reverse
        url = url + '&sort_reverse=' + (newsr and '1' or '0')
        return '<a href="%s">%s</a>' % (escape(url, 1), escape(name))


InitializeClass(AcceleratedHTTPCacheManager)


manage_addAcceleratedHTTPCacheManagerForm = DTMLFile('dtml/addAccel',
                                                     globals())

def manage_addAcceleratedHTTPCacheManager(self, id, REQUEST=None):
    ' '
    self._setObject(id, AcceleratedHTTPCacheManager(id))
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)

# FYI good resource: http://www.web-caching.com/proxy-caches.html
