
import Interface

class C:
    def m1(self, a, b):
        "return 1"
        return 1

    def m2(self, a, b):
        "return 2"
        return 2

# testInstancesOfClassImplements

IC=Interface.impliedInterface(C)

C.__implements__=IC

class I1(Interface.Base):
    def ma(self):
        "blah"

class I2(I1): pass

class I3(Interface.Base): pass

class I4(Interface.Base): pass

class A(I1.deferred()):
    __implements__=I1

class B:
    __implements__=I2, I3

class D(A, B): pass

class E(A, B):
    __implements__ = A.__implements__, C.__implements__


class FooInterface(Interface.Base):
    """ This is an Abstract Base Class """

    foobar = Interface.Attribute("fuzzed over beyond all recognition")

    def aMethod(self, foo, bar, bingo):
        """ This is aMethod """

    def anotherMethod(self, foo=6, bar="where you get sloshed", bingo=(1,3,)):
        """ This is anotherMethod """

    def wammy(self, zip, *argues):
        """ yadda yadda """

    def useless(self, **keywords):
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

FunInterface = Interface.new('FunInterface')
BarInterface = Interface.new('BarInterface', [FunInterface])
BobInterface = Interface.new('BobInterface')
BazInterface = Interface.new('BazInterface', [BobInterface, BarInterface])
