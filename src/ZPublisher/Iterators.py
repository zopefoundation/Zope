import io

from zope.interface import Interface
from zope.interface import implementer


class IUnboundStreamIterator(Interface):
    """
    An iterator with unknown length that can be published.
    """

    def __next__():
        """
        Return a sequence of bytes out of the bytestream, or raise
        StopIeration if we've reached the end of the bytestream.
        """


class IStreamIterator(IUnboundStreamIterator):
    """
    An iterator with known length that can be published.

    IStreamIterators must not read from the object database.
    After the application finishes interpreting a request and
    returns an iterator to be processed asynchronously, it closes
    the ZODB connection. If the iterator then tries to load some
    ZODB object, ZODB would do one of two things.  If the connection
    is still closed, ZODB would raise an error. If the connection
    happens to be re-opened by another thread, ZODB might allow it,
    but it has a chance of going insane if it happens to be loading
    or storing something in the other thread at the same time.
    """

    def __len__():
        """
        Return an integer representing the length of the object
        in bytes.
        """


@implementer(IStreamIterator)
class filestream_iterator(io.FileIO):
    """
    A FileIO subclass which implements an iterator that returns a
    fixed-sized sequence of bytes.
    """

    def __init__(self, name, mode='rb', bufsize=-1, streamsize=1 << 16):
        super().__init__(name, mode)
        self.streamsize = streamsize

    def __next__(self):
        data = self.read(self.streamsize)
        if not data:
            raise StopIteration
        return data

    next = __next__

    def __len__(self):
        cur_pos = self.tell()
        self.seek(0, io.SEEK_END)
        size = self.tell()
        self.seek(cur_pos, io.SEEK_SET)
        return size
