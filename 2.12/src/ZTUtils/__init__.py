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
"""Package of template utility classes and functions.

$Id$
"""
# BBB 2005/05/01 -- to be removed after 12 months
import zope.deferredimport
zope.deferredimport.define(
    Iterator = 'ZTUtils.Iterator:Iterator'
    )

from Tree import encodeExpansion, decodeExpansion, a2b, b2a
from SimpleTree import SimpleTreeMaker

__allow_access_to_unprotected_subobjects__ = 1
__roles__ = None

from ZTUtils.Zope import Batch, TreeMaker, SimpleTreeMaker, LazyFilter
from ZTUtils.Zope import url_query, make_query, make_hidden_input
