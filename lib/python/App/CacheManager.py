#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
#
############################################################################## 
__doc__='''Cache management support


$Id: CacheManager.py,v 1.2 1997/11/07 17:06:02 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import Globals
import time

class CacheManager:
    """Cache management mix-in
    """
    _cache_age=60
    _cache_size=2000

    manage_cacheForm=Globals.HTMLFile('App/cache')

    def cache_length(self): return len(Globals.Bobobase._jar.cache)

    def database_size(self): return len(Globals.Bobobase._jar.db.index)

    def cache_age(self): return self._cache_age
    def manage_cache_age(self,value,REQUEST):
	"set cache age"
	if self._p_jar.db is not Globals.Bobobase:
	    raise 'Session Error', (
		'''You may not change the database cache age
		while working in a <em>session</em>''')
	self._cache_age=Globals.Bobobase._jar.cache.cache_age=value
	return self.manage_cacheForm(self,REQUEST)

    def cache_size(self): return self._cache_size
    def manage_cache_size(self,value,REQUEST):
	"set cache size"
	if self._p_jar.db is not Globals.Bobobase:
	    raise 'Session Error', (
		'''You may not change the database cache size
		while working in a <em>session</em>''')
	self._cache_size=Globals.Bobobase._jar.cache.cache_size=value
	return self.manage_cacheForm(self,REQUEST)

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
	return self.manage_cacheForm(self,REQUEST)

    def manage_minimize(self,value,REQUEST):
	"Perform a full sweep through the cache"
	Globals.Bobobase._jar.cache.minimize(value)
	return self.manage_cacheForm(self,REQUEST)

    def initialize_cache(self):
	Globals.Bobobase._jar.cache.cache_size=self._cache_size
	Globals.Bobobase._jar.cache.cache_age =self._cache_age

    def cache_detail(self):
	detail={}
	for oid, ob in Globals.Bobobase._jar.cache.items():
	    c=ob.__class__.__name__
	    if detail.has_key(c): detail[c]=detail[c]+1
	    else: detail[c]=1
	detail=detail.items()
	detail.sort()
	return detail

############################################################################## 
#
# $Log: CacheManager.py,v $
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
