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
"""Access control exceptions
"""

import zExceptions

class Unauthorized(zExceptions.Unauthorized):

    def getValueName(self):
        v=self.value
        n=getattr(v, 'getId', v)
        if n is v:  n=getattr(v, 'id', v)
        if n is v:  n=getattr(v, '__name__', v)
        if n is not v:
            if callable(n):
                try: n = n()
                except TypeError: pass
            return n

        c = getattr(v, '__class__', type(v))
        c = getattr(c, '__name__', 'object')
        return "a particular %s" % c
