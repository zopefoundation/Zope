from zope.interface.verify import verifyClass
from ZPublisher.Iterators import filestream_iterator
from ZPublisher.Iterators import IStreamIterator

import unittest


class TestFileStreamIterator(unittest.TestCase):

    def testInterface(self):
        verifyClass(IStreamIterator, filestream_iterator)
