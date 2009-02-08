##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Stick directory information in the built-in namespace."""

__version__='$Revision: 1.13 $'[11:-2]

import __builtin__
import os
import sys

import Products
from App.Common import package_home


try:
    home = os.environ['SOFTWARE_HOME']
except KeyError:
    import Zope2
    home = os.path.abspath(package_home(Zope2.__dict__))

    home, e = os.path.split(home)
    d, e = os.path.split(home)
    if e == '.':
        home = d
    d, e = os.path.split(home)
    if e == '..':
        home = os.path.dirname(d)

home = os.path.realpath(home)
__builtin__.SOFTWARE_HOME = SOFTWARE_HOME = home

try:
    zhome = os.environ['ZOPE_HOME']
except KeyError:
    zhome = os.path.join(home, '..', '..')

__builtin__.ZOPE_HOME = ZOPE_HOME = os.path.realpath(zhome)

try:
    chome = os.environ['INSTANCE_HOME']
except KeyError:
    chome = home
    d, e = os.path.split(chome)
    if e == 'python':
        d, e = os.path.split(d)
        if e == 'lib':
            chome = d or os.getcwd()
else:
    chome = os.path.realpath(chome)
    inst_ppath = os.path.join(chome, 'lib', 'python')
    if os.path.isdir(inst_ppath):
        sys.path.insert(0, inst_ppath)

__builtin__.INSTANCE_HOME = INSTANCE_HOME = chome

# CLIENT_HOME allows ZEO clients to easily keep distinct pid and
# log files. This is currently an *experimental* feature, as I expect
# that increasing ZEO deployment will cause bigger changes to the
# way that z2.py works fairly soon.
try:
    CLIENT_HOME = os.environ['CLIENT_HOME']
except KeyError:
    CLIENT_HOME = os.path.join(INSTANCE_HOME, 'var')

__builtin__.CLIENT_HOME = CLIENT_HOME

# If there is a Products package in INSTANCE_HOME, add it to the
# Products package path
ip = os.path.join(INSTANCE_HOME, 'Products')
ippart = 0
ppath = Products.__path__
if os.path.isdir(ip) and ip not in ppath:
    disallow = os.environ.get('DISALLOW_LOCAL_PRODUCTS', '').lower()
    if disallow in ('no', 'off', '0', ''):
        ppath.insert(0, ip)
        ippart = 1

ppathpat = os.environ.get('PRODUCTS_PATH', None)
if ppathpat is not None:
    psep = os.pathsep
    if ppathpat.find('%(') >= 0:
        newppath = (ppathpat % {
            'PRODUCTS_PATH': psep.join(ppath ),
            'SOFTWARE_PRODUCTS': psep.join(ppath[ippart:] ),
            'INSTANCE_PRODUCTS': ip,
            }).split(psep)
    else:
        newppath = ppathpat.split(psep)
    del ppath[:]
    for p in filter(None, newppath):
        p = os.path.abspath(p)
        if os.path.isdir(p) and p not in ppath:
            ppath.append(p)
