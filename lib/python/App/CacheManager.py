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
__doc__='''Cache management support


$Id: CacheManager.py,v 1.24 2002/03/27 10:14:00 htrd Exp $'''
__version__='$Revision: 1.24 $'[11:-2]

import Globals, time, sys

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

    def cache_detail_length(self):
      try: db=self._p_jar.db()
      except:
          return ()
      else: return db.cacheDetailSize()

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

    def manage_minimize(self,value=1,REQUEST=None):
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
            return '\n'.join(map(lambda (name, count): '%6d %s' %
                                   (count, name), detail))
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
            return '\n'.join(res)
        else:
            # raw
            return detail

Globals.default__class_init__(CacheManager)

