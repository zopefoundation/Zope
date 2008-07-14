import warnings

# The Z2 Interface module is deprecated:  in Zope 2.12, this module will use
# Z3 interfaces instead.  Meanwhile, silence the deprecation warning.
_existing_filters = warnings.filters[:]
warnings.filterwarnings('ignore', category=DeprecationWarning)
try:
    from Interface import Interface
finally:
    warnings.filters[:] = _existing_filters
    del _existing_filters

class IStreamIterator(Interface):
    """
    An iterator that can be published.

    IStreamIterators must not read from the object database.
    After the application finishes interpreting a request and 
    returns an iterator to be processed asynchronously, it closes 
    the ZODB connection. If the iterator then tries to load some 
    ZODB object, ZODB would do one of two things.  If the connection 
    is still closed, ZODB would raise an error. If the connection 
    happens to be re-opened by another thread, ZODB might allow it, 
    but it has a chance of going insane if it happens to be loading 
    or storing something in the other thread at the same time.                      """

    def next():
        """
        Return a sequence of bytes out of the bytestream, or raise
        StopIeration if we've reached the end of the bytestream.
        """

    def __len__():
        """
        Return an integer representing the length of the object
        in bytes.
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

    def __len__(self):
        cur_pos = self.tell()
        self.seek(0, 2)
        size = self.tell()
        self.seek(cur_pos, 0)
    
        return size
