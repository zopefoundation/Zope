#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1998 Digital Creations, Inc., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''Standard routines for handling Principia Extensions

Principia extensions currently include external methods and pluggable brains.

$Id: Extensions.py,v 1.1 1998/08/03 13:43:26 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

from string import find
import os, zlib, rotor
path_split=os.path.split
exists=os.path.exists
    
class FuncCode:

    def __init__(self, f, im=0):
	self.co_varnames=f.func_code.co_varnames[im:]
	self.co_argcount=f.func_code.co_argcount-im

    def __cmp__(self,other):
	return cmp((self.co_argcount, self.co_varnames),
		   (other.co_argcount, other.co_varnames))


def getObject(module, name, reload=0, modules={}):

    if modules.has_key(module):
        old=modules[module]
        if old.has_key(name) and not reload: return old[name]
    else:
        old=None
    
    d,n = path_split(module)
    if d: raise ValueError, (
        'The file name, %s, should be a simple file name' % module)
    m={}
    d=find(n,'.')
    if d > 0:
        d,n=n[:d],n[d+1:]
        n=("%s/lib/python/Products/%s/Extensions/%s.pyp"
           % (SOFTWARE_HOME,d,n))
        __traceback_info__=n, module
        if exists(n):
            data=zlib.decompress(
                rotor.newrotor(d+' shshsh').decrypt(open(n).read())
                )
            exec compile(data,module,'exec') in m
        else:       
            exec open("%s/Extensions/%s.py" %
                      (SOFTWARE_HOME, module)) in m
    else:
        exec open("%s/Extensions/%s.py" % (SOFTWARE_HOME, module)) in m

    r=m[name]
    if old:
        for k, v in m.items(): old[k]=v
    else: modules[module]=m

    return r

class NoBrains: pass

def getBrain(module, class_name, reload=0):
    'Check/load a class'

    if not module and not class_name: return NoBrains

    try: c=getObject(module, class_name, reload)
    except KeyError, v:
        if v == class_name: raise ValueError, (
            'The class, %s, is not defined in file, %s' % (class_name, module))

    if not hasattr(c,'__bases__'): raise ValueError, (
	'%s, is not a class' % class_name)
    
    return c


############################################################################## 
#
# $Log: Extensions.py,v $
# Revision 1.1  1998/08/03 13:43:26  jim
# new folderish control panel and product management
#
#
