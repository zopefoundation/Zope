#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################## 
__doc__='''Cache management support


$Id: CacheManager.py,v 1.8 1998/11/10 14:55:53 brian Exp $'''
__version__='$Revision: 1.8 $'[11:-2]

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
	return Globals.Bobobase._jar.cache.cache_mean_age

    def cache_mean_deal(self):
	return Globals.Bobobase._jar.cache.cache_mean_deal

    def cache_mean_deac(self):
	return Globals.Bobobase._jar.cache.cache_mean_deac

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

############################################################################## 
#
# $Log: CacheManager.py,v $
# Revision 1.8  1998/11/10 14:55:53  brian
# Fixed typo in cache manager
#
# Revision 1.7  1998/08/03 13:43:00  jim
#       - New folderish control panel that separates database and
#         product management into separate interfaces.
#
# Revision 1.6  1998/03/24 16:39:11  jim
# Changed to give more likely database size.
#
# Revision 1.5  1998/02/05 15:20:21  jim
# Lowered cache size.
#
# Revision 1.4  1997/12/18 16:45:29  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.3  1997/11/19 20:11:48  jim
# Fixed bugs in check for working in a session.
#
# Revision 1.2  1997/11/07 17:06:02  jim
# added session checks.
#
# Revision 1.1  1997/09/19 15:55:52  jim
# *** empty log message ***
#
# Revision 1.1  1997/06/30 15:25:37  jim
# *** empty log message ***
#
#
