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
import Acquisition

class B(Base):
    color='red'

class A(Acquisition.Implicit):
    def hi(self):
        print "%s()" % self.__class__.__name__, self.color

b=B()
b.a=A()
b.a.hi()
b.a.color='green'
b.a.hi()
try:
    A().hi()
    raise 'Program error', 'spam'
except AttributeError: pass

#
#   New test for wrapper comparisons.
#
foo = b.a
bar = b.a
assert( foo == bar )
c = A()
b.c = c
b.c.d = c
assert( b.c.d == c )
assert( b.c.d == b.c )
assert( b.c == c )


def checkContext(self, o):
    # Python equivalent to aq_inContextOf
    from Acquisition import aq_base, aq_parent, aq_inner
    subob = self
    o = aq_base(o)
    while 1:
        if aq_base(subob) is o: return 1
        self = aq_inner(subob)
        if self is None: break
        subob = aq_parent(self)
        if subob is None: break


assert checkContext(b.c, b)
assert not checkContext(b.c, b.a)

assert b.a.aq_inContextOf(b)
assert b.c.aq_inContextOf(b)
assert b.c.d.aq_inContextOf(b)
assert b.c.d.aq_inContextOf(c)
assert b.c.d.aq_inContextOf(b.c)
assert not b.c.aq_inContextOf(foo)
assert not b.c.aq_inContextOf(b.a)
assert not b.a.aq_inContextOf('somestring')
