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
__doc__='''Cache management support


$Id: CacheManager.py,v 1.21 2001/08/27 19:25:19 shane Exp $'''
__version__='$Revision: 1.21 $'[11:-2]

import Globals, time, sys, string

class CacheManager:
    """Cache management mix-in
    """
    _cache_age=60
    _cache_size=400
    _vcache_age=60
    _vcache_size=400

    manage_cacheParameters=Globals.DTMLFile('dtml/cacheParameters', globals())
    manage_cacheGC=Globals.DTMLFile('dtml/cacheGC', globals())

    def cache_length(self):
        try: db=self._p_jar.db()
        except:
            # BoboPOS2
            return len(Globals.Bobobase._jar.cache)
        else: return db.cacheSize()

    def database_size(self):
        try: db=self._p_jar.db()
        except:
            # BoboPOS2
            return len(Globals.Bobobase._jar.db.index)*4
        else: return db.objectCount()

    def cache_age(self):
        try:
            if self._p_jar.getVersion():
                return self._vcache_age
        except: pass

        return self._cache_age

    def manage_cache_age(self,value,REQUEST):
        "set cache age"
        try:
            v=self._p_jar.getVersion()
        except:
            # BoboPOS2:
            if self._p_jar.db is not Globals.Bobobase._jar.db:
                raise 'Version Error', (
                    '''You may not change the database cache age
                    while working in a <em>version</em>''')
            self._cache_age=Globals.Bobobase._jar.cache.cache_age=value
        else:
            if v:
                self._vcache_age=value
                self._p_jar.db().setVersionCacheDeactivateAfter(value)
            else:
                self._cache_age=value
                self._p_jar.db().setCacheDeactivateAfter(value)

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheParameters')



    def cache_size(self):
        try:
            if self._p_jar.getVersion():
                return self._vcache_size
        except: pass
        return self._cache_size

    def manage_cache_size(self,value,REQUEST):
        "set cache size"
        try:
            v=self._p_jar.getVersion()
        except: 
            # BoboPOS2:
            if self._p_jar.db is not Globals.Bobobase._jar.db:
                raise 'Version Error', (
                    '''You may not change the database cache size
                    while working in a <em>version</em>''')
            self._cache_size=Globals.Bobobase._jar.cache.cache_size=value
        else:
            if v:
                self._vcache_size=value
                self._p_jar.db().setVersionCacheSize(value)
            else:
                self._cache_size=value
                self._p_jar.db().setCacheSize(value)

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheParameters')


    def cacheStatistics(self):
        try: return self._p_jar.db().cacheStatistics()
        except: pass

        # BoboPOS 2
        return (
            ('Mean time since last access (minutes)',
             "%.4g" % (Globals.Bobobase._jar.cache.cache_mean_age/60.0)),
            ('Deallocation rate (objects/minute)',
             "%.4g" % (Globals.Bobobase._jar.cache.cache_mean_deal*60)),
            ('Deactivation rate (objects/minute)',
             "%.4g" % (Globals.Bobobase._jar.cache.cache_mean_deac*60)),
            ('Time of last cache garbage collection',
             time.asctime(time.localtime(
                 Globals.Bobobase._jar.cache.cache_last_gc_time
                 ))
             ),
            )
        

    # BoboPOS 2
    def cache_mean_age(self):
        return Globals.Bobobase._jar.cache.cache_mean_age/60.0

    # BoboPOS 2
    def cache_mean_deal(self):
        return Globals.Bobobase._jar.cache.cache_mean_deal*60

    # BoboPOS 2
    def cache_mean_deac(self):
        return Globals.Bobobase._jar.cache.cache_mean_deac*60

    # BoboPOS 2
    def cache_last_gc_time(self):
        t=Globals.Bobobase._jar.cache.cache_last_gc_time
        return time.asctime(time.localtime(t))

    def manage_full_sweep(self,value,REQUEST):
        "Perform a full sweep through the cache"
        try: db=self._p_jar.db()
        except:
            # BoboPOS2
            Globals.Bobobase._jar.cache.full_sweep(value)
        else: db.cacheFullSweep(value)

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheGC')

    def manage_minimize(self,value,REQUEST):
        "Perform a full sweep through the cache"
        try: db=self._p_jar.db()
        except:
            # BoboPOS2
            Globals.Bobobase._jar.cache.minimize(value)
        else: db.cacheMinimize(value)

        if REQUEST is not None:
            response=REQUEST['RESPONSE']
            response.redirect(REQUEST['URL1']+'/manage_cacheGC')

    def initialize_cache(self):
        try: db=self._p_jar.db()
        except:
            # BoboPOS2
            Globals.Bobobase._jar.cache.cache_size=self._cache_size
            Globals.Bobobase._jar.cache.cache_age =self._cache_age
        else:
            db.setCacheSize(self._cache_size)
            db.setCacheDeactivateAfter(self._cache_age)
            db.setVersionCacheSize(self._vcache_size)
            db.setVersionCacheDeactivateAfter(self._vcache_age)

    def cache_detail(self, REQUEST=None):
        """
        Returns the name of the classes of the objects in the cache
        and the number of objects in the cache for each class.
        """
        db=self._p_jar.db()
        detail = db.cacheDetail()
        if REQUEST is not None:
            # format as text
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
            return string.join(map(lambda (name, count): '%6d %s' %
                                   (count, name), detail), '\n')
        else:
            # raw
            return detail

    def cache_extreme_detail(self, REQUEST=None):
        """
        Returns information about each object in the cache.
        """
        db=self._p_jar.db()
        detail = db.cacheExtremeDetail()
        if REQUEST is not None:
            # sort the list.
            lst = map(lambda dict: ((dict['conn_no'], dict['oid']), dict),
                      detail)
            lst.sort()
            # format as text.
            res = [
                '# Table shows connection number, oid, refcount, state, '
                'and class.',
                '# States: L = loaded, G = ghost, C = changed']
            for sortkey, dict in lst:
                id = dict.get('id', None)
                if id:
                    idinfo = ' (%s)' % id
                else:
                    idinfo = ''
                s = dict['state']
                if s == 0:
                    state = 'L'  # loaded
                elif s == 1:
                    state = 'C'  # changed
                else:
                    state = 'G'  # ghost
                res.append('%d %-34s %6d %s %s%s' % (
                    dict['conn_no'], `dict['oid']`, dict['rc'],
                    state, dict['klass'], idinfo))
            REQUEST.RESPONSE.setHeader('Content-Type', 'text/plain')
            return string.join(res, '\n')
        else:
            # raw
            return detail

Globals.default__class_init__(CacheManager)

