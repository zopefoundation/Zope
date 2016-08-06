import unittest
from zope.interface.verify import verifyClass
from ZPublisher.Iterators import IStreamIterator, filestream_iterator


class TestFileStreamIterator(unittest.TestCase):

    def testInterface(self):
        verifyClass(IStreamIterator, filestream_iterator)
