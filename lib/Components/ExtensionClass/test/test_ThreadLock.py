
import ThreadLock, thread
from rand import rand
from time import sleep

from ExtensionClass import Base

with_lock=1

class P(Base):

    def __oldcall_method__(self,f,a,k={}):
        if with_lock:
            try: lock=self.lock
            except AttributeError: return apply(f,a,k)
        else: return apply(f,a,k)
        try:
            lock.acquire()
            return apply(f,a,k)
        finally:
            lock.release()

    __call_method__=apply

    def __init__(self,*args,**kw):
        self.count=0
        if with_lock:
            self.lock=lock=ThreadLock.allocate_lock()
            self.__call_method__=lock.guarded_apply

    def inc(self):
            c=self.count
            sleep(rand()/32768.0)
            self.count=self.count+1
            return c,self.count

    def incn(self,n):
            c=self.count
            for i in range(n): self.inc()
            return c,self.count
        
p=P(1,2,spam=3)

def test():
    
    for i in range(10):
        n=3
        old,new=p.incn(n)
        print old,new
        if old+n != new: print 'oops'


for i in range(10): thread.start_new_thread(test,())
sleep(50)
