import unittest

class RecordTests( unittest.TestCase ):

    def test_repr( self ):
        from ZPublisher.HTTPRequest import record
        record = record()
        record.a = 1
        record.b = 'foo'
        r = repr( record )
        d = eval( r )
        self.assertEqual( d, record.__dict__ )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RecordTests, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main()
