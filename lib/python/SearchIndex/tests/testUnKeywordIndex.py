##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
import os, sys
execfile(os.path.join(sys.path[0], 'framework.py'))

import ZODB
from SearchIndex.UnKeywordIndex import UnKeywordIndex

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
        Test KeywordIndex objects.
    """

    def setUp( self ):
        """
        """
        self._index = UnKeywordIndex( 'foo' )
        self._marker = []
        self._values = [ ( 0, Dummy( ['a'] ) )
                       , ( 1, Dummy( ['a','b'] ) )
                       , ( 2, Dummy( ['a','b','c'] ) )
                       , ( 3, Dummy( ['a','b','c', 'a'] ) )
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

    def testAddObjectWOKeywords(self):


        import zLOG

        def log_write(subsystem, severity, summary, detail, error,
                      PROBLEM=zLOG.PROBLEM):
            if severity >= PROBLEM:
                assert 0, "%s(%s): %s" % (subsystem, severity, summary)

        old_log_write=zLOG.log_write
        zLOG.log_write=log_write
        try:
            self._populateIndex()
            self._index.index_object(999, None)
        finally:
            zLOG.log_write=old_log_write
    
    def testEmpty( self ):
        assert len( self._index ) == 0
        assert len( self._index.referencedObjects() ) == 0

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

        for k, v in values:
            assert self._index.getEntryForObject( k ) == v.foo()

        assert (len( self._index.uniqueValues( 'foo' ) ) == len( values )-1,
                len(values)-1)

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

framework()
