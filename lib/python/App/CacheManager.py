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


$Id: CacheManager.py,v 1.11 1999/03/10 00:14:55 klm Exp $'''
__version__='$Revision: 1.11 $'[11:-2]

import Globals, time, sys

class CacheManager:
    """Cache management mix-in
    """
    _cache_age=60
    _cache_size=400

    manage_cacheParameters=Globals.HTMLFile('cacheParameters', globals())
    manage_cacheGC=Globals.HTMLFile('cacheGC', globals())

    def cache_length(self): return len(Globals.Bobobase._jar.cache)

    def database_size(self): return len(Globals.Bobobase._jar.db.index)*4

    def cache_age(self): return self._cache_age
    def manage_cache_age(self,value,REQUEST):
        "set cache age"
        if self._p_jar.db is not Globals.Bobobase._jar.db:
            raise 'Session Error', (
                '''You may not change the database cache age
                while working in a <em>session</em>''')
        self._cache_age=Globals.Bobobase._jar.cache.cache_age=value
        return self.manage_CacheParameters(self,REQUEST)

    def cache_size(self): return self._cache_size
    def manage_cache_size(self,value,REQUEST):
        "set cache size"
        if self._p_jar.db is not Globals.Bobobase._jar.db:
            raise 'Session Error', (
                '''You may not change the database cache size
                while working in a <em>session</em>''')
        self._cache_size=Globals.Bobobase._jar.cache.cache_size=value
        return self.manage_cacheParameters(self,REQUEST)

    def cache_mean_age(self):
        return Globals.Bobobase._jar.cache.cache_mean_age/60.0

    def cache_mean_deal(self):
        return Globals.Bobobase._jar.cache.cache_mean_deal*60

    def cache_mean_deac(self):
        return Globals.Bobobase._jar.cache.cache_mean_deac*60

    def cache_last_gc_time(self):
        t=Globals.Bobobase._jar.cache.cache_last_gc_time
        return time.asctime(time.localtime(t))

    def manage_full_sweep(self,value,REQUEST):
        "Perform a full sweep through the cache"
        Globals.Bobobase._jar.cache.full_sweep(value)
        return self.manage_cacheGC(self,REQUEST)

    def manage_minimize(self,value,REQUEST):
        "Perform a full sweep through the cache"
        Globals.Bobobase._jar.cache.minimize(value)
        return self.manage_cacheGC(self,REQUEST)

    def initialize_cache(self):
        Globals.Bobobase._jar.cache.cache_size=self._cache_size
        Globals.Bobobase._jar.cache.cache_age =self._cache_age

    def cache_detail(self):
        detail={}
        for oid, ob in Globals.Bobobase._jar.cache.items():
            c="%s.%s" % (ob.__class__.__module__, ob.__class__.__name__)
            if detail.has_key(c): detail[c]=detail[c]+1
            else: detail[c]=1
        detail=detail.items()
        detail.sort()
        return detail

    def cache_extreme_detail(self):
        detail=[]
        rc=sys.getrefcount
        db=Globals.Bobobase._jar.db
        for oid, ob in Globals.Bobobase._jar.cache.items():
            id=oid
            if hasattr(ob,'__dict__'):
                d=ob.__dict__
                if d.has_key('id'):
                    id="%s (%s)" % (oid, d['id'])
                elif d.has_key('__name__'):
                    id="%s (%s)" % (oid, d['__name__'])

            detail.append({
                'oid': id,
                'klass': "%s.%s" % (ob.__class__.__module__,
                                    ob.__class__.__name__),
                'rc': rc(ob)-4,
                'references': db.objectReferencesIn(oid),
                })
        return detail
