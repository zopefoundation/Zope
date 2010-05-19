##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""KeywordIndex unit tests.

$Id$
"""

import unittest
import Testing
import Zope2
Zope2.startup()

from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex


class Dummy:

    def __init__( self, foo ):
        self._foo = foo

    def foo( self ):
        return self._foo

    def __str__( self ):
        return '<Dummy: %s>' % self._foo

    __repr__ = __str__

def sortedUnique(seq):
    unique = {}
    for i in seq:
        unique[i] = None
    unique = unique.keys()
    unique.sort()
    return unique


class TestKeywordIndex( unittest.TestCase ):
    """
        Test KeywordIndex objects.
    """
    _old_log_write = None

    def setUp( self ):
        """
        """
        self._index = KeywordIndex( 'foo' )
        self._marker = []
        self._values = [ ( 0, Dummy( ['a'] ) )
                       , ( 1, Dummy( ['a','b'] ) )
                       , ( 2, Dummy( ['a','b','c'] ) )
                       , ( 3, Dummy( ['a','b','c','a'] ) )
                       , ( 4, Dummy( ['a', 'b', 'c', 'd'] ) )
                       , ( 5, Dummy( ['a', 'b', 'c', 'e'] ) )
                       , ( 6, Dummy( ['a', 'b', 'c', 'e', 'f'] ))
                       , ( 7, Dummy( [0] ) )
                       ]
        self._noop_req  = { 'bar': 123 }
        self._all_req = { 'foo': ['a'] }
        self._some_req = { 'foo': ['e'] }
        self._overlap_req = { 'foo': ['c', 'e'] }
        self._string_req = {'foo': 'a'}
        self._zero_req  = { 'foo': [0] }

    def tearDown( self ):
        """
        """

    def _populateIndex( self ):
        for k, v in self._values:
            self._index.index_object( k, v )

    def _checkApply( self, req, expectedValues ):
        result, used = self._index._apply_index( req )
        assert used == ( 'foo', )
        assert len(result) == len( expectedValues ), \
          '%s | %s' % ( map( None, result ),
                        map(lambda x: x[0], expectedValues ))

        if hasattr(result, 'keys'): result=result.keys()
        for k, v in expectedValues:
            assert k in result

    def test_z3interfaces(self):
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass

        verifyClass(IPluggableIndex, KeywordIndex)
        verifyClass(ISortIndex, KeywordIndex)
        verifyClass(IUniqueValueIndex, KeywordIndex)

    def testAddObjectWOKeywords(self):

        try:
            self._populateIndex()
            self._index.index_object(999, None)
        finally:
            pass

    def testEmpty( self ):
        assert len( self._index ) == 0
        assert len( self._index.referencedObjects() ) == 0
        self.assertEqual(self._index.numObjects(), 0)

        assert self._index.getEntryForObject( 1234 ) is None
        assert ( self._index.getEntryForObject( 1234, self._marker )
                  is self._marker ), self._index.getEntryForObject(1234)
        self._index.unindex_object( 1234 ) # nothrow

        assert self._index.hasUniqueValuesFor( 'foo' )
        assert not self._index.hasUniqueValuesFor( 'bar' )
        assert len( self._index.uniqueValues( 'foo' ) ) == 0

        assert self._index._apply_index( self._noop_req ) is None
        self._checkApply( self._all_req, [] )
        self._checkApply( self._some_req, [] )
        self._checkApply( self._overlap_req, [] )
        self._checkApply( self._string_req, [] )

    def testPopulated( self ):
        self._populateIndex()
        values = self._values

        #assert len( self._index ) == len( values )
        assert len( self._index.referencedObjects() ) == len( values )

        assert self._index.getEntryForObject( 1234 ) is None
        assert ( self._index.getEntryForObject( 1234, self._marker )
                  is self._marker )
        self._index.unindex_object( 1234 ) # nothrow
        self.assertEqual(self._index.indexSize(), len( values )-1)

        for k, v in values:
            entry = self._index.getEntryForObject( k )
            entry.sort()
            kw = sortedUnique(v.foo())
            self.assertEqual(entry, kw)

        assert len( self._index.uniqueValues( 'foo' ) ) == len( values )-1
        assert self._index._apply_index( self._noop_req ) is None

        self._checkApply( self._all_req, values[:-1])
        self._checkApply( self._some_req, values[ 5:7 ] )
        self._checkApply( self._overlap_req, values[2:7] )
        self._checkApply( self._string_req, values[:-1] )

    def testZero( self ):
        self._populateIndex()
        values = self._values
        self._checkApply( self._zero_req, values[ -1: ] )
        assert 0 in self._index.uniqueValues( 'foo' )

    def testReindexChange(self):
        self._populateIndex()
        expected = Dummy(['x', 'y'])
        self._index.index_object(6, expected)
        result, used = self._index._apply_index({'foo': ['x', 'y']})
        result=result.keys()
        assert len(result) == 1
        assert result[0] == 6
        result, used = self._index._apply_index(
            {'foo': ['a', 'b', 'c', 'e', 'f']}
            )
        result = result.keys()
        assert 6 not in result

    def testReindexNoChange(self):
        self._populateIndex()
        expected = Dummy(['foo', 'bar'])
        self._index.index_object(8, expected)
        result, used = self._index._apply_index(
            {'foo': ['foo', 'bar']})
        result = result.keys()
        assert len(result) == 1
        assert result[0] == 8
        self._index.index_object(8, expected)
        result, used = self._index._apply_index(
            {'foo': ['foo', 'bar']})
        result = result.keys()
        assert len(result) == 1
        assert result[0] == 8

    def testIntersectionWithRange(self):
        # Test an 'and' search, ensuring that 'range' doesn't mess it up.
        self._populateIndex()

        record = { 'foo' : { 'query'  : [ 'e', 'f' ]
                           , 'operator' : 'and'
                           }
                 }
        self._checkApply( record, self._values[6:7] )

        #
        #   Make sure that 'and' tests with incompatible paramters
        #   don't return empty sets.
        #
        record[ 'foo' ][ 'range' ] = 'min:max'
        self._checkApply( record, self._values[6:7] )

    def testDuplicateKeywords(self):
        try:
            self._index.index_object(0, Dummy(['a', 'a', 'b', 'b']))
            self._index.unindex_object(0)
        finally:
            pass

    def testCollectorIssue889(self) :
        # Test that collector issue 889 is solved
        values = self._values
        nonexistent = 'foo-bar-baz'
        self._populateIndex()
        # make sure key is not indexed
        result = self._index._index.get(nonexistent, self._marker)
        assert result is self._marker
        # patched _apply_index now works as expected
        record = {'foo' : { 'query'    : [nonexistent]
                          , 'operator' : 'and'}
                 }
        self._checkApply(record, [])
        record = {'foo' : { 'query'    : [nonexistent, 'a']
                          , 'operator' : 'and'}
                 }
        # and does not break anything
        self._checkApply(record, [])
        record = {'foo' : { 'query'    : ['d']
                          , 'operator' : 'and'}
                 }
        self._checkApply(record, values[4:5])
        record = {'foo' : { 'query'    : ['a', 'e']
                          , 'operator' : 'and'}
                 }
        self._checkApply(record, values[5:7])

    def test_noindexing_when_noattribute(self):
        to_index = Dummy(['hello'])
        self._index._index_object(10, to_index, attr='UNKNOWN')
        self.failIf(self._index._unindex.get(10))
        self.failIf(self._index.getEntryForObject(10))

    def test_noindexing_when_raising_attribute(self):
        class FauxObject:
            def foo(self):
                raise AttributeError
        to_index = FauxObject()
        self._index._index_object(10, to_index, attr='foo')
        self.failIf(self._index._unindex.get(10))
        self.failIf(self._index.getEntryForObject(10))

    def test_value_removes(self):
        
        to_index = Dummy(['hello'])
        self._index._index_object(10, to_index, attr='foo')
        self.failUnless(self._index._unindex.get(10))

        to_index = Dummy('')
        self._index._index_object(10, to_index, attr='foo')
        self.failIf(self._index._unindex.get(10))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestKeywordIndex ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
