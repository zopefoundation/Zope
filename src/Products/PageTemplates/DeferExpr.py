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

from zope.deferredimport import deprecated


# BBB Zope 5.0
deprecated(
    'Please import from zope.tales.expressions.',
    DeferExpr='zope.tales.expressions:DeferExpr',
    DeferWrapper='zope.tales.expressions:DeferWrapper',
    LazyExpr='zope.tales.expressions:LazyExpr',
    LazyWrapper='zope.tales.expressions:LazyWrapper',
)
