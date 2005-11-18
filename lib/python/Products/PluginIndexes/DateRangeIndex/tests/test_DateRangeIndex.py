##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""DateRangeIndex unit tests.

$Id$
"""

import unittest
import Testing
import Zope2
Zope2.startup()

import sys

from Products.PluginIndexes.DateRangeIndex.DateRangeIndex import DateRangeIndex


class Dummy:

    def __init__( self, name, start, stop ):

        self._name  = name
        self._start = start
        self._stop  = stop

    def name( self ):

        return self._name

    def start( self ):

        return self._start

    def stop( self ):

        return self._stop

    def datum( self ):

        return ( self._start, self._stop )

dummies = [ Dummy( 'a', None,   None )
          , Dummy( 'b', None,   None )
          , Dummy( 'c', 0,      None )
          , Dummy( 'd', 10,     None )
          , Dummy( 'e', None,   4    )
          , Dummy( 'f', None,   11   )
          , Dummy( 'g', 0,      11   )
          , Dummy( 'h', 2,      9    )
          ]

def matchingDummies( value ):
    result = []

    for dummy in dummies:

        if ( ( dummy.start() is None or dummy.start() <= value )
         and ( dummy.stop() is None or dummy.stop() >= value )
           ):
            result.append( dummy )

    return result


class DRI_Tests( unittest.TestCase ):

    def setUp( self ):
        pass

    def tearDown( self ):
        pass

    def test_z3interfaces(self):
        from Products.PluginIndexes.interfaces import IDateRangeIndex
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass

        verifyClass(IDateRangeIndex, DateRangeIndex)
        verifyClass(IPluggableIndex, DateRangeIndex)
        verifyClass(ISortIndex, DateRangeIndex)
        verifyClass(IUniqueValueIndex, DateRangeIndex)

    def test_empty( self ):

        empty = DateRangeIndex( 'empty' )

        assert empty.getEntryForObject( 1234 ) is None
        empty.unindex_object( 1234 ) # shouldn't throw

        assert not empty.uniqueValues( 'foo' )
        assert not empty.uniqueValues( 'foo', 1 )

        assert empty._apply_index( { 'zed' : 12345 } ) is None

        result, used = empty._apply_index( { 'empty' : 12345 } )

        assert not result
        assert used == ( None, None )

    def test_retrieval( self ):

        work = DateRangeIndex( 'work', 'start', 'stop' )

        for i in range( len( dummies ) ):
            work.index_object( i, dummies[i] )

        for i in range( len( dummies ) ):
            assert work.getEntryForObject( i ) == dummies[i].datum()

        for value in range( -1, 15 ):

            matches = matchingDummies( value )
            results, used = work._apply_index( { 'work' : value } )
            assert used == ( 'start', 'stop' )

            assert len( matches ) == len( results ), ( '%s: %s == %s'
               % ( value, map( lambda x: x.name(), matches ), results ) )

            matches.sort( lambda x, y: cmp( x.name(), y.name() ) )

            for result, match in map( None, results, matches ):
                assert work.getEntryForObject( result ) == match.datum()

    def test_longdates( self ):
        self.assertRaises(OverflowError, self._badlong )

    def _badlong(self):
        work = DateRangeIndex ('work', 'start', 'stop' )
        bad = Dummy( 'bad', long(sys.maxint) + 1, long(sys.maxint) + 1 )
        work.index_object( 0, bad )


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DRI_Tests ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
