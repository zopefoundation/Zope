##############################################################################
#
# Copyright (c) 1996-2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
import ExtensionClass

class C(ExtensionClass.Base):

    def __call_method__(self, meth, args, kw={}):
        print 'give us a hook, hook, hook...'
        return apply(meth, args, kw)

    def hi(self, *args, **kw):
        print "%s()" % self.__class__.__name__, args, kw

c=C()
c.hi()
c.hi(1,2,3)
c.hi(1,2,spam='eggs')
