
import Interface

class C:
    def m1(self, a, b):
        "return 1"
        return 1

    def m2(self, a, b):
        "return 2"
        return 2

IC=Interface.impliedInterface(C)

print "should be 0:", IC.implementedByInstancesOf(C)

C.__implements__=IC

print "should be 1:", IC.implementedByInstancesOf(C)

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
        c.__name__, Interface.implementedByInstancesOf(c))

print
for c in A, B, C, D, E:
    print "an instance of %s implements: %s" % (
        c.__name__,
        Interface.implementedBy(c()))

for i in I1, I2, I3, I4, IC:
    print
    for c in A, B, C, D, E:
        print "%s is implemented by instances of %s? %s" % (
               i.__name__, c.__name__,
               i.implementedByInstancesOf(c))
    print
    for c in A, B, C, D, E:
        print "%s is implemented by an instance of %s? %s" % (
               i.__name__, c.__name__,
               i.implementedBy(c()))
    
a=A()
try:
    a.ma()
    print "something's wrong, this should have failed!"
except:
    pass

