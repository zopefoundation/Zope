import thread
from ZOutPipe import OutputPipe

class ZRendevous:

    def __init__(self, n=1, name='Main'):
        sync=thread.allocate_lock()
        self._a=sync.acquire
        self._r=sync.release
        pool=[]
        self._lists=pool, [], []
        self._a()
        try:
            while n > 0:
                l=thread.allocate_lock()
                l.acquire()
                pool.append(l)
                thread.start_new_thread(ZServerPublisher,
                                        (name, self.accept,))
                n=n-1
        finally: self._r()

    def accept(self):
        self._a()
        try:
            pool, requests, ready = self._lists
            while not requests:
                l=pool[-1]
                del pool[-1]
                ready.append(l)
                self._r()
                l.acquire()
                self._a()
                pool.append(l)

            r=self.requests[0]
            del self.requets[0]
            return r
        finally: self._r()

    def handle(self, environ, input):
        output=OutputPipe()
        self._a()
        try:
            pool, requests, ready = self._lists
            requests.append((input, output, environ))
            if ready:
                l=ready[-1]
                del ready[-1]
                l.release()
            return output
        finally: self._r()
