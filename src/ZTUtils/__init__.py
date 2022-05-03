##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Package of template utility classes and functions.
"""
from AccessControl.SecurityInfo import ModuleSecurityInfo

from .Tree import a2b  # NOQA: F401
from .Tree import b2a  # NOQA: F401
from .Tree import decodeExpansion  # NOQA: F401
from .Tree import encodeExpansion  # NOQA: F401
from .Zope import Batch  # NOQA: F401
from .Zope import LazyFilter  # NOQA: F401
from .Zope import SimpleTreeMaker  # NOQA: F401
from .Zope import TreeMaker  # NOQA: F401
from .Zope import make_hidden_input  # NOQA: F401
from .Zope import make_query  # NOQA: F401
from .Zope import url_query  # NOQA: F401


security = ModuleSecurityInfo('ZTUtils')

for name in ('encodeExpansion', 'decodeExpansion', 'a2b', 'b2a',
             'Batch', 'TreeMaker', 'SimpleTreeMaker', 'LazyFilter',
             'url_query', 'make_query', 'make_hidden_input'):
    security.declarePublic(name)  # NOQA: D001
