import unittest
from zope.interface.verify import verifyClass
from ZPublisher.Iterators import IStreamIterator, filestream_iterator

class TestFileStreamIterator(unittest.TestCase):
    def testInterface(self):
        verifyClass(IStreamIterator, filestream_iterator)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestFileStreamIterator ) )
    return suite

def main():
    unittest.main(defaultTest='test_suite')

if __name__ == '__main__':
    main()
