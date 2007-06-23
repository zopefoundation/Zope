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
"""TALES

BBB 2005/05/01 -- to be removed after 12 months

$Id$
"""
from zope.tales.tests.simpleexpr import SimpleExpr
from zope.tales.tales import ExpressionEngine as Engine
from zope.tales.tales import _default as Default
from Products.PageTemplates.Expressions import SafeMapping

import zope.deprecation
zope.deprecation.moved("zope.tales.tales", "2.12")
