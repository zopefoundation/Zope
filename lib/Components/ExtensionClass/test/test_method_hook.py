
import ExtensionClass

class C(ExtensionClass.Base):

    def __call_method__(self,meth,args,kw={}):
        print 'give us a hook, hook, hook...'
        apply(meth,args,kw)

    def hi(self,*args,**kw): print self, args, kw

c=C()
c.hi()
c.hi(1,2,3)
c.hi(1,2,spam='eggs')
