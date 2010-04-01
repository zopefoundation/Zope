##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''short description


$Id$'''
__version__='$Revision: 1.8 $'[11:-2]

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
