"""ZServer output pipe
"""

import thread
from ZEvent import Wakeup
from string import join
TupleType=type(())

class OutputPipe:
    """A pipe which can be written to and read from different threads.
    Also supports callbacks to notify readers when the pipe has been
    written to or has been closed."""

    def __init__(self,callback=None):
        "callback should be a tuple (function,(args,))"
        lock=thread.allocate_lock()
        self._r=lock.release
        self._a=lock.acquire
        self._buf=[]
        self._callback=callback

    def write(self, text):
        self._a()
        try:
            self._buf.append(text)
        finally: self._r()
        self.notify()

    def notify(self):
        if self._callback:
            fun=self._callback[0]
            args=self._callback[1]+(self,)
            Wakeup(lambda f=fun,a=args: apply(f,a))
        else:
            Wakeup()

    def close(self):
        self._a()
        try:
            b=self._buf
            if b: self._buf=tuple(b)
            else: self._buf=None
        finally: self._r()
        self.notify()

    def read(self):
        """Read data from the pipe

        Return None if the pipe is open but has no data.
        Return an empty string if the pipe is closed.
        """
        self._a()
        try:
            b=self._buf
            if b is None: return ''
            if not b: return None
            if type(b) is TupleType: self._buf=None
            else:                    self._buf=[]
            return join(b,'')
        finally: self._r()
