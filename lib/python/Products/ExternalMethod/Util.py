#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved. 
#
############################################################################## 
__doc__='''Utility routines that are handy for developers

$Id: Util.py,v 1.1 1998/03/18 23:13:28 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

standard_reload=reload
import Globals, sys

class_map={} # waaaa


def Reload(module):
    classes=[]
    __import__(module)
    m=sys.modules[module]
    for k, v in m.__dict__.items():
	if (hasattr(v,'__bases__') and hasattr(v,'__name__')
	    and hasattr(v,'__dict__') and hasattr(v,'__module__')
	    and v.__module__==module):
	    # OK, smells like a class
	    cn="%s.%s" % (module, k)
	    if class_map.has_key(cn): v=class_map[cn]
	    else: class_map[cn]=v
	    classes.append((k,v))
    
    try: reload(m)
    except TypeError, v: raise 'spam', v, sys.exc_traceback
    m=sys.modules[module]
    r=''
    for name, klass in classes:
	if hasattr(m,name):
	    c=getattr(m,name)
	    d=klass.__dict__
	    for k, v in c.__dict__.items():
		d[k]=v
	    if r: r="%s, %s" % (r, name)
	    else: r=name

    Globals.Bobobase._jar.cache.minimize(0)

    return r or 'No classes affected'


############################################################################## 
#
# $Log: Util.py,v $
# Revision 1.1  1998/03/18 23:13:28  jim
# initial
#
#
