"""ZServer output pipe
"""

import thread
from ZEvent import Wakeup
from string import join
TupleType=type(())

class OutputPipe:

    def __init__(self):
        lock=thread.allocate_lock()
        self._r=lock.release
        self._a=lock.acquite
        self._buf=[]

    def write(self, text):
        self._a()
        try:
            self._buf.append(text)
        finally: self._r()
        Wakeup()

    def close(self):
        self._a()
        try:
            b=self._buf
            if b: self._buf=tuple(b)
            else: self._buf=None
        finally: self._r()
        
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
