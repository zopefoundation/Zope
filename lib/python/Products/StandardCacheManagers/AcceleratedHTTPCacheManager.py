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
'''
Accelerated HTTP cache manager --
  Adds caching headers to the response so that downstream caches will
  cache according to a common policy.

$Id$
'''

from OFS.Cache import Cache, CacheManager
from OFS.SimpleItem import SimpleItem
import time
import Globals
from Globals import DTMLFile
import urlparse, httplib
from cgi import escape
from urllib import quote
from App.Common import rfc1123_date


class AcceleratedHTTPCache (Cache):
    # Note the need to take thread safety into account.
    # Also note that objects of this class are not persistent,
    # nor do they use acquisition.
    def __init__(self):
        self.hit_counts = {}

    def initSettings(self, kw):
        # Note that we lazily allow AcceleratedHTTPCacheManager
        # to verify the correctness of the internal settings.
        self.__dict__.update(kw)

    def ZCache_invalidate(self, ob):
        # Note that this only works for default views of objects.
        phys_path = ob.getPhysicalPath()
        if self.hit_counts.has_key(phys_path):
            del self.hit_counts[phys_path]
        ob_path = quote('/'.join(phys_path))
        results = []
        for url in self.notify_urls:
            if not url:
                continue
            # Send the PURGE request to each HTTP accelerator.
            if url[:7].lower() == 'http://':
                u = url
            else:
                u = 'http://' + url
            (scheme, host, path, params, query, fragment
             ) = urlparse.urlparse(u)
            if path[-1:] == '/':
                p = path[:-1] + ob_path
            else:
                p = path + ob_path
            h = httplib.HTTPConnection(host)
            h.request('PURGE', p)
            r = h.getresponse()
            results.append('%s %s' % (r.status, r.reason))
        return 'Server response(s): ' + ';'.join(results)

    def ZCache_get(self, ob, view_name, keywords, mtime_func, default):
        return default

    def ZCache_set(self, ob, data, view_name, keywords, mtime_func):
        # Note the blatant ignorance of view_name, keywords, and
        # mtime_func.  Standard HTTP accelerators are not able to make
        # use of this data.
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

    __ac_permissions__ = (
        ('View management screens', ('getSettings',
                                     'manage_main',
                                     'manage_stats',
                                     'getCacheReport',
                                     'sort_link')),
        ('Change cache managers', ('manage_editProps',), ('Manager',)),
        )

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
            cache = AcceleratedHTTPCache()
            cache.initSettings(self._settings)
            caches[cacheid] = cache
            return cache

    def getSettings(self):
        ' '
        return self._settings.copy()  # Don't let DTML modify it.

    manage_main = DTMLFile('dtml/propsAccel', globals())

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


Globals.default__class_init__(AcceleratedHTTPCacheManager)


manage_addAcceleratedHTTPCacheManagerForm = DTMLFile('dtml/addAccel',
                                                     globals())

def manage_addAcceleratedHTTPCacheManager(self, id, REQUEST=None):
    ' '
    self._setObject(id, AcceleratedHTTPCacheManager(id))
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)

# FYI good resource: http://www.web-caching.com/proxy-caches.html
