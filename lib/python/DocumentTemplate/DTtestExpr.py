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
__doc__='''short description


$Id: DTtestExpr.py,v 1.1 1997/09/22 15:13:17 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

from DocumentTemplate import *
import sys

def test1():
    print HTML('area code=<!--#var expr="phone[:3]"-->')(phone='7035551212')

def test2():
    print HTML('area code=<!--#var expr="phone.number"-->')(phone='7035551212')

def test3():
    print HTML('area code=<!--#var expr="phone*1000"-->')(phone='7035551212')

def test4():

    h=HTML(
	"""
	<!--#if expr="level==1"-->
	level was 1
	<!--#elif expr="level==2"-->
	level was 2
	<!--#elif expr="level==3"-->
	level was 3
	<!--#else-->
	level was something else
	<!--#endif-->
	""")

    for i in range(4):
	print '-' * 77
	print i, h(level=i)
    print '-' * 77
    

if __name__ == "__main__":
    try: command=sys.argv[1]
    except: command='main'
    globals()[command]()

############################################################################## 
#
# $Log: DTtestExpr.py,v $
# Revision 1.1  1997/09/22 15:13:17  jim
# *** empty log message ***
#
#
