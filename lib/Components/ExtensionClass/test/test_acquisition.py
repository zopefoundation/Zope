from ExtensionClass import Base
import Acquisition

class B(Base):
    color='red'

class A(Acquisition.Implicit):
    def hi(self): print self, self.color

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
