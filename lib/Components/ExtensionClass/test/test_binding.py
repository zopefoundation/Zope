
from ExtensionClass import Base
from MethodObject import Method

class foo(Method):
  def __call__(self,ob,*args,**kw): print 'called', ob, args, kw

class bar(Base):
  hi=foo()

x=bar()
hi=x.hi
print hi
hi(1,2,3,name='spam')

