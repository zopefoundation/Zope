##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.
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

# Requirements:
#
# All: BerkeleyDB 4.1.25, available from www.sleepycat.com
# Python 2.2: PyBSDDB 4.1.3 or better, from pybsddb.sf.net
# Python 2.3: nothing extra

try:
    from bsddb import db
except ImportError:
    try:
        from bsddb3 import db
    except ImportError:
        db = None

# This flag tells other components whether Berkeley storage is available
is_available = bool(db)

# Useful constants
ZERO = '\0'*8
