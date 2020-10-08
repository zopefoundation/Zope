import unittest

from zope.interface.verify import verifyClass
from ZPublisher.Iterators import IStreamIterator
from ZPublisher.Iterators import filestream_iterator


class TestFileStreamIterator(unittest.TestCase):

    def testInterface(self):
        verifyClass(IStreamIterator, filestream_iterator)
