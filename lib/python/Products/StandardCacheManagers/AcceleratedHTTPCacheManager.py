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
from urllib import quote
from string import lower, join, split


def http_date(value, format='%a, %d %b %Y %H:%M:%S GMT'):
    return time.strftime(format, time.gmtime(value))


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
        ob_path = quote(join(phys_path, '/'))
        results = []
        for url in self.notify_urls:
            if not url:
                continue
            # Send the PURGE request to each HTTP accelerator.
            if lower(url[:7]) == 'http://':
                u = url
            else:
                u = 'http://' + url
            (scheme, host, path, params, query, fragment
             ) = urlparse.urlparse(u)
            if path[-1:] == '/':
                p = path[:-1] + ob_path
            else:
                p = path + ob_path
            h = httplib.HTTP(host)
            h.putrequest('PURGE', p)
            h.endheaders()
            errcode, errmsg, headers = h.getreply()
            h.getfile().read()  # Mandatory for httplib?
            results.append('%s %s' % (errcode, errmsg))
        return 'Server response(s): ' + join(results, ';')

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
        expires=http_date(time.time() + seconds)
        # RESPONSE.setHeader('Last-Modified', http_date(time.time()))
        RESPONSE.setHeader('Cache-Control', 'max-age=%d' % seconds)
        RESPONSE.setHeader('Expires', expires)


caches = {}
PRODUCT_DIR = split(__name__, '.')[-2]

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
            rval.append({'path': join(path, '/'),
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
        return '<a href="%s">%s</a>' % (url, name)


Globals.default__class_init__(AcceleratedHTTPCacheManager)


manage_addAcceleratedHTTPCacheManagerForm = DTMLFile('dtml/addAccel',
                                                     globals())

def manage_addAcceleratedHTTPCacheManager(self, id, REQUEST=None):
    ' '
    self._setObject(id, AcceleratedHTTPCacheManager(id))
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)

# FYI good resource: http://www.web-caching.com/proxy-caches.html
