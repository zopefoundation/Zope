##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Interpreter for a pre-compiled TAL program.

BBB 2005/05/01 -- to be removed after 12 months

$Id$
"""
import zope.deprecation
zope.deprecation.moved('zope.tal.talinterpreter', '2.12')

import zope.deferredimport
zope.deferredimport.deprecated(
    "'interpolate' has moved to zope.i18n.  This reference will be gone "
    "in Zope 2.12.",
    interpolate = 'zope.i18n:interpolate'
    )
