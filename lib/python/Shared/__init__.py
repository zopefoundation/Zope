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
__doc__='''$Id: __init__.py,v 1.2 1997/12/02 14:57:16 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]


import sys, string, os

__.__path__.append("%s/bin-%s/%s" % (
    __.__path__[0], string.split(sys.version)[0], sys.platform))
    
############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.2  1997/12/02 14:57:16  jim
# *** empty log message ***
#
# Revision 1.1  1997/09/25 18:57:45  jim
# *** empty log message ***
#
#
