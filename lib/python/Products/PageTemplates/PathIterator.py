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

"""Path Iterator

A TALES Iterator with the ability to use first() and last() on
subpaths of elements.
"""

__version__='$Revision: 1.4 $'[11:-2]

import TALES
from Expressions import restrictedTraverse, Undefs, getSecurityManager

class Iterator(TALES.Iterator):
    def __bobo_traverse__(self, REQUEST, name):
        if name in ('first', 'last'):
            path = REQUEST['TraversalRequestNameStack']
            names = list(path)
            names.reverse()
            path[:] = [tuple(names)]
        return getattr(self, name)

    def same_part(self, name, ob1, ob2):
        if name is None:
            return ob1 == ob2
        if isinstance(name, type('')):
            name = name.split('/')
        name = filter(None, name)
        securityManager = getSecurityManager()
        try:
            ob1 = restrictedTraverse(ob1, name, securityManager)
            ob2 = restrictedTraverse(ob2, name, securityManager)
        except Undefs:
            return 0
        return ob1 == ob2
