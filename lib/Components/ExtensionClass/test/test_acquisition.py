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

