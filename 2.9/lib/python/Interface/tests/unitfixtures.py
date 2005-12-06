##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
from Interface import Interface
from Interface.Attribute import Attribute

class mytest(Interface):
    pass

class C:
    def m1(self, a, b):
        "return 1"
        return 1

    def m2(self, a, b):
        "return 2"
        return 2

# testInstancesOfClassImplements




#  YAGNI IC=Interface.impliedInterface(C)
class IC(Interface):
    def m1(a, b):
        "return 1"

    def m2(a, b):
        "return 2"



C.__implements__=IC

class I1(Interface):
    def ma():
        "blah"

class I2(I1): pass

class I3(Interface): pass

class I4(Interface): pass

class A(I1.deferred()):
    __implements__=I1

class B:
    __implements__=I2, I3

class D(A, B): pass

class E(A, B):
    __implements__ = A.__implements__, C.__implements__


class FooInterface(Interface):
    """ This is an Abstract Base Class """

    foobar = Attribute("fuzzed over beyond all recognition")

    def aMethod(foo, bar, bingo):
        """ This is aMethod """

    def anotherMethod(foo=6, bar="where you get sloshed", bingo=(1,3,)):
        """ This is anotherMethod """

    def wammy(zip, *argues):
        """ yadda yadda """

    def useless(**keywords):
        """ useless code is fun! """

class Foo:
    """ A concrete class """

    __implements__ = FooInterface,

    foobar = "yeah"

    def aMethod(self, foo, bar, bingo):
        """ This is aMethod """
        return "barf!"

    def anotherMethod(self, foo=6, bar="where you get sloshed", bingo=(1,3,)):
        """ This is anotherMethod """
        return "barf!"

    def wammy(self, zip, *argues):
        """ yadda yadda """
        return "barf!"

    def useless(self, **keywords):
        """ useless code is fun! """
        return "barf!"

foo_instance = Foo()

class Blah:
    pass

new = Interface.__class__
FunInterface = new('FunInterface')
BarInterface = new('BarInterface', [FunInterface])
BobInterface = new('BobInterface')
BazInterface = new('BazInterface', [BobInterface, BarInterface])
