
from Sync import Synchronized
import thread
from rand import rand
from time import sleep


class P(Synchronized):

    def __init__(self,*args,**kw):
        self.count=0

    def inc(self):
            c=self.count
            sleep(rand()/327680.0)
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
