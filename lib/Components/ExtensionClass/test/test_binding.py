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
from ExtensionClass import Base
from MethodObject import Method

class foo(Method):
    def __call__(self, ob, *args, **kw):
        print 'called', ob, args, kw

class bar(Base):
    def __repr__(self):
        return "bar()"
    hi = foo()

x=bar()
hi=x.hi
print type(hi)
hi(1,2,3,name='spam')
