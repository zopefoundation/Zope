from Interface import Interface

class IStreamIterator(Interface):
    def next(self):
        """
        Return a sequence of bytes out of the bytestream, or raise
        StopIeration if we've reached the end of the bytestream.
        """
class filestream_iterator(file):
    """
    a file subclass which implements an iterator that returns a
    fixed-sized sequence of bytes.
    """

    __implements__ = (IStreamIterator,)

    def __init__(self, name, mode='r', bufsize=-1, streamsize=1<<16):
        file.__init__(self, name, mode, bufsize)
        self.streamsize = streamsize

    def next(self):
        data = self.read(self.streamsize)
        if not data:
            raise StopIteration
        return data
    
    
