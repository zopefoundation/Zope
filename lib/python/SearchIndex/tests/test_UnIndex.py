import Zope
import unittest
from SearchIndex.UnIndex import UnIndex

class Dummy:

    def __init__( self, foo ):
        self._foo = foo

    def foo( self ):
        return self._foo
    
    def __str__( self ):
        return '<Dummy: %s>' % self._foo
    
    __repr__ = __str__

class TestCase( unittest.TestCase ):
    """
        Test FieldIndex objects.
    """

    def setUp( self ):
        """
        """
        self._index = UnIndex( 'foo' )
        self._marker = []
        self._values = [ ( 0, Dummy( 'a' ) )
                       , ( 1, Dummy( 'ab' ) )
                       , ( 2, Dummy( 'abc' ) )
                       , ( 3, Dummy( 'abca' ) )
                       , ( 4, Dummy( 'abcd' ) )
                       , ( 5, Dummy( 'abce' ) )
                       , ( 6, Dummy( 'abce' ) )
                       ]
        self._forward = {}
        self._backward = {}
        for k, v in self._values:
            self._backward[k] = v
            keys = self._forward.get( v, [] )
            self._forward[v] = keys
            
        self._noop_req  = { 'bar': 123 }
        self._request   = { 'foo': 'abce' }
        self._min_req   = { 'foo': 'abc'
                          , 'foo_usage': 'range:min'
                          }
        self._max_req   = { 'foo': 'abc'
                          , 'foo_usage': 'range:max'
                          }
        self._range_req = { 'foo': ( 'abc', 'abcd' )
                          , 'foo_usage': 'range:min:max'
                          }


    def tearDown( self ):
        """
        """

    def _populateIndex( self ):
        for k, v in self._values:
            self._index.index_object( k, v )
    
    def _checkApply( self, req, expectedValues ):
        result, used = self._index._apply_index( req )
        assert used == ( 'foo', )
        assert len( result ) == len( expectedValues ), \
          '%s | %s' % ( map( None, result ), expectedValues )
        for k, v in expectedValues:
            assert k in result
    
    def testEmpty( self ):
        # Test an empty FieldIndex.

        assert len( self._index ) == 0
        assert len( self._index.referencedObjects() ) == 0

        assert self._index.getEntryForObject( 1234 ) is None
        assert ( self._index.getEntryForObject( 1234, self._marker )
                  is self._marker )
        self._index.unindex_object( 1234 ) # nothrow

        assert self._index.hasUniqueValuesFor( 'foo' )
        assert not self._index.hasUniqueValuesFor( 'bar' )
        assert len( self._index.uniqueValues( 'foo' ) ) == 0

        assert self._index._apply_index( self._noop_req ) is None
        self._checkApply( self._request, [] )
        self._checkApply( self._min_req, [] )
        self._checkApply( self._max_req, [] )
        self._checkApply( self._range_req, [] )
    
    def testPopulated( self ):
        self._populateIndex()
        values = self._values

        assert len( self._index ) == len( values )
        assert len( self._index.referencedObjects() ) == len( values )

        assert self._index.getEntryForObject( 1234 ) is None
        assert ( self._index.getEntryForObject( 1234, self._marker )
                  is self._marker )
        self._index.unindex_object( 1234 ) # nothrow

        for k, v in values:
            assert self._index.getEntryForObject( k ) == v.foo()

        assert len( self._index.uniqueValues( 'foo' ) ) == len( values )-1

        assert self._index._apply_index( self._noop_req ) is None

        self._checkApply( self._request, self._values[ -2: ] )
        self._checkApply( self._min_req, self._values[ 2: ] )
        self._checkApply( self._max_req, self._values[ :3 ] )
        self._checkApply( self._range_req, self._values[ 2:5 ] )


def test_suite():
    return unittest.makeSuite( TestCase )


if __name__ == '__main__':
    unittest.TextTestRunner().run( test_suite() )
