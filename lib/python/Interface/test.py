
import Interface

class C:
    def m1(self, a, b):
        "return 1"
        return 1

    def m2(self, a, b):
        "return 2"
        return 2

IC=Interface.impliedInterface(C)

print "should be 0:", IC.isImplementedByInstancesOf(C)

C.__implements__=IC

print "should be 1:", IC.isImplementedByInstancesOf(C)

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

print
for c in A, B, C, D, E:
    print "%s implements: %s" % (
        c.__name__, Interface.instancesOfObjectImplements(c))

print
for c in A, B, C, D, E:
    print "an instance of %s implements: %s" % (
        c.__name__,
        Interface.objectImplements(c()))

for i in I1, I2, I3, I4, IC:
    print
    for c in A, B, C, D, E:
        print "%s is implemented by instances of %s? %s" % (
               i.__name__, c.__name__,
               i.isImplementedByInstancesOf(c))
    print
    for c in A, B, C, D, E:
        print "%s is implemented by an instance of %s? %s" % (
               i.__name__, c.__name__,
               i.isImplementedBy(c()))
    
a=A()
try:
    a.ma()
    print "something's wrong, this should have failed!"
except:
    pass




FooInterface = Interface.new('FooInterface')

print Interface.interface_as_stx(FooInterface)

BarInterface = Interface.new('BarInterface', [FooInterface])

print Interface.interface_as_stx(BarInterface)

BobInterface = Interface.new('BobInterface')
BazInterface = Interface.new('BazInterface', [BobInterface, BarInterface])

print Interface.interface_as_stx(BazInterface)

ints = [BazInterface, BobInterface, BarInterface, FooInterface]

for int in ints:
    for int2 in ints:
        if int.extends(int2):
            print "%s DOES extend %s" % (int.__name__, int2.__name__)
        else:
            print "%s DOES NOT extend %s" % (int.__name__, int2.__name__)

print "\n"

# methods and pretty printing

class AnAbstractBaseClass:
    """ This is an Abstract Base Class """

    foobar = "fuzzed over beyond all recognition"

    def aMethod(self, foo, bar, bingo):
        """ This is aMethod """
        pass

    def anotherMethod(self, foo=6, bar="where you get sloshed", bingo=(1,3,)):
        """ This is anotherMethod """
        pass

    def wammy(self, zip, *argues):
        """ yadda yadda """
        pass

    def useless(self, **keywords):
        """ useless code is fun! """
        pass

AnABCInterface = Interface.impliedInterface(AnAbstractBaseClass)

print Interface.interface_as_stx(AnABCInterface)

class AConcreteClass:
    """ A concrete class """

    __implements__ = AnABCInterface,

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

concrete_instance = AConcreteClass()

class Blah:
    pass

blah_instance = Blah()

if AnABCInterface.isImplementedBy(concrete_instance):
    print "%s is an instance that implements %s" % (concrete_instance, AnABCInterface.__name__)

if AnABCInterface.isImplementedByInstancesOf(AConcreteClass):
    print "%s is a class that implements %s" % (AConcreteClass, AnABCInterface.__name__)

if not AnABCInterface.isImplementedBy(blah_instance):
    print "%s is NOT an instance that implements %s" % (blah_instance, AnABCInterface.__name__)

if not AnABCInterface.isImplementedByInstancesOf(Blah):
    print "%s is NOT a class that implements %s" % (Blah, AnABCInterface.__name__)





