##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

# Python 2.2 and earlier requires the pybsddb distutils package, but for
# Python 2.3, we really want to use the standard bsddb package.  Also, we want
# to set a flag that other modules can easily tests to see if this stuff is
# available or not.  Python 2.2 and 2.3 has bool() but not Python 2.1.
#
# Get the pybsddb extension module from pybsddb.sourceforge.net and the
# BerkeleyDB libraries from www.sleepycat.com.

try:
    bool
except NameError:
    def bool(x):
        return not not x

try:
    from bsddb import _db as db
except ImportError:
    try:
        from bsddb3 import db
    except ImportError:
        db = None

is_available = bool(db)
