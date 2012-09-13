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
"""
# BBB 2005/05/01 -- to be removed after 12 months
import zope.deferredimport
zope.deferredimport.define(
    Iterator = 'ZTUtils.Iterator:Iterator'
    )

from AccessControl.SecurityInfo import ModuleSecurityInfo
security = ModuleSecurityInfo('ZTUtils')

security.declarePublic('encodeExpansion', 'decodeExpansion', 'a2b', 'b2a')
from Tree import encodeExpansion, decodeExpansion, a2b, b2a

security.declarePublic('SimpleTreeMaker')
from SimpleTree import SimpleTreeMaker

security.declarePublic('Batch', 'TreeMaker', 'SimpleTreeMaker', 'LazyFilter')
from ZTUtils.Zope import Batch, TreeMaker, SimpleTreeMaker, LazyFilter

security.declarePublic('url_query', 'make_query', 'make_hidden_input')
from ZTUtils.Zope import url_query, make_query, make_hidden_input
