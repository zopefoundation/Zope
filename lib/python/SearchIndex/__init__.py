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
__doc__='''Collected utilities to support database indexing.


$Id: __init__.py,v 1.1 1997/09/15 16:07:23 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import sys, string, os

__path__=__.__path__

for o in 's', 'r':
    try: 
	s=os.popen('uname -s').read()[:-1]
	r=os.popen('uname -r').read()[:-1]
	if r and s:
	    p=(string.lower(s)+r)
	    if p: __path__.append("%s/bin-%s/%s" % (
		__path__[0], string.split(sys.version)[0], p))
    except: pass

__path__.append("%s/bin-%s/%s" % (
    __path__[0], string.split(sys.version)[0], sys.platform))
    
    
    


############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.1  1997/09/15 16:07:23  jim
# *** empty log message ***
#
#
