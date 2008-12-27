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
"""Shared global data

o N.B.:  DO NOT IMPORT ANYTHING HERE!  This module is just for shared data!
"""
__version__='$Revision: 1.56 $'[11:-2]

DevelopmentMode = False

# Global constants: __replaceable__ flags:
NOT_REPLACEABLE = 0
REPLACEABLE = 1
UNIQUE = 2

VersionNameName='Zope-Version'

# XXX ZODB stashes the main database object here
opened = []
