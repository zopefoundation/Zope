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
"""Path Iterator

BBB 2005/05/01 -- to be removed after 12 months

$Id$
"""
import zope.deferredimport
zope.deferredimport.deprecated(
    "It has been renamed to PathIterator and moved to the "
    "Products.PageTemplates.Expressions module.  This reference will be "
    "gone in Zope 2.12.",
    PathIterator = "Products.PageTemplates.Expressions:PathIterator"
    )
