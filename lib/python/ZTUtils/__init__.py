##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Package of template utility classes and functions.

$Id: __init__.py,v 1.6 2002/08/14 22:10:12 mj Exp $'''
__version__='$Revision: 1.6 $'[11:-2]

from Batch import Batch
from Iterator import Iterator
from Tree import TreeMaker, encodeExpansion, decodeExpansion, a2b, b2a
from SimpleTree import SimpleTreeMaker

import sys
if sys.modules.has_key('Zope'):
    del sys
    __allow_access_to_unprotected_subobjects__ = 1
    __roles__ = None

    from Zope import Batch, TreeMaker, SimpleTreeMaker, LazyFilter
    from Zope import url_query, make_query, make_hidden_input
