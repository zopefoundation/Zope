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

"""Commonly used utility functions."""

__version__='$Revision: 1.7 $'[11:-2]

import os, sys, Products, string
from Common import package_home
path_join = os.path.join
path_split = os.path.split

try: home=os.environ['SOFTWARE_HOME']
except:
    home=package_home(Products.__dict__)
    if not os.path.isabs(home):
        home=path_join(os.getcwd(), home)
        
    home,e=path_split(home)
    if path_split(home)[1]=='.': home=path_split(home)[0]
    if path_split(home)[1]=='..':
        home=path_split(path_split(home)[0])[0]

sys.modules['__builtin__'].SOFTWARE_HOME=SOFTWARE_HOME=home

try:
    chome=os.environ['INSTANCE_HOME']
except:
    chome=home
    d,e=path_split(chome)
    if e=='python':
        d,e=path_split(d)
        if e=='lib': chome=d or os.getcwd()
else:
    inst_ppath = path_join(chome, 'lib', 'python')
    if os.path.isdir(inst_ppath):
        sys.path.insert(0, inst_ppath)

sys.modules['__builtin__'].INSTANCE_HOME=INSTANCE_HOME=chome

# CLIENT_HOME allows ZEO clients to easily keep distinct pid and
# log files. This is currently an *experimental* feature, as I expect
# that increasing ZEO deployment will cause bigger changes to the
# way that z2.py works fairly soon.
try:    CLIENT_HOME = os.environ['CLIENT_HOME']
except: CLIENT_HOME = path_join(INSTANCE_HOME, 'var')

sys.modules['__builtin__'].CLIENT_HOME=CLIENT_HOME

# If there is a Products package in INSTANCE_HOME, add it to the
# Products package path
ip=path_join(INSTANCE_HOME, 'Products')
ippart = 0
ppath = Products.__path__
if os.path.isdir(ip) and ip not in ppath:
    disallow=string.lower(os.environ.get('DISALLOW_LOCAL_PRODUCTS',''))
    if disallow in ('no', 'off', '0', ''):
        ppath.insert(0, ip)
        ippart = 1
        
ppathpat = os.environ.get('PRODUCTS_PATH', None)
if ppathpat is not None:
    psep = os.pathsep
    if string.find(ppathpat, '%(') >= 0:
        newppath = string.split(ppathpat % {
            'PRODUCTS_PATH': string.join(ppath, psep),
            'SOFTWARE_PRODUCTS': string.join(ppath[ippart:], psep),
            'INSTANCE_PRODUCTS': ip,
            }, psep)
    else:
        newppath = string.split(ppathpat, psep)
    del ppath[:]
    for p in filter(None, newppath):
        p = os.path.abspath(p)
        if os.path.isdir(p) and p not in ppath:
            ppath.append(p)
