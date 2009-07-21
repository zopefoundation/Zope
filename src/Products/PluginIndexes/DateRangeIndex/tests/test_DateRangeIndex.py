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

        self.failUnless(empty.getEntryForObject( 1234 ) is None)
        empty.unindex_object( 1234 ) # shouldn't throw

        self.failIf(empty.uniqueValues( 'foo' ))
        self.failIf(empty.uniqueValues( 'foo', 1 ))

        self.failUnless(empty._apply_index( { 'zed' : 12345 } ) is None)

        result, used = empty._apply_index( { 'empty' : 12345 } )

        self.failIf(result)
        self.assertEqual(used, ( None, None ))

    def test_retrieval( self ):

        work = DateRangeIndex( 'work', 'start', 'stop' )

        for i in range( len( dummies ) ):
            work.index_object( i, dummies[i] )

        for i in range( len( dummies ) ):
            self.assertEqual(work.getEntryForObject( i ), dummies[i].datum())

        for value in range( -1, 15 ):

            matches = matchingDummies( value )
            results, used = work._apply_index( { 'work' : value } )
            self.assertEqual(used, ( 'start', 'stop' ))

            self.assertEqual(len( matches ), len( results ))

            matches.sort( lambda x, y: cmp( x.name(), y.name() ) )

            for result, match in map( None, results, matches ):
                self.assertEqual(work.getEntryForObject(result), match.datum())

    def test_longdates( self ):
        self.assertRaises(OverflowError, self._badlong )

    def _badlong(self):
        work = DateRangeIndex ('work', 'start', 'stop' )
        bad = Dummy( 'bad', long(sys.maxint) + 1, long(sys.maxint) + 1 )
        work.index_object( 0, bad )

    def test_datetime(self):
        from datetime import datetime
        before = datetime(2009, 7, 11, 0, 0)
        start = datetime(2009, 7, 13, 5, 15)
        between = datetime(2009, 7, 13, 5, 45)
        stop = datetime(2009, 7, 13, 6, 30)
        after = datetime(2009, 7, 14, 0, 0)

        dummy = Dummy('test', start, stop)
        work = DateRangeIndex( 'work', 'start', 'stop' )
        work.index_object(0, dummy)

        self.assertEqual(work.getEntryForObject(0), (20790915, 20790990))

        results, used = work._apply_index( { 'work' : before } )
        self.assertEqual(len(results), 0)

        results, used = work._apply_index( { 'work' : start } )
        self.assertEqual(len(results), 1)

        results, used = work._apply_index( { 'work' : between } )
        self.assertEqual(len(results), 1)

        results, used = work._apply_index( { 'work' : stop } )
        self.assertEqual(len(results), 1)

        results, used = work._apply_index( { 'work' : after } )
        self.assertEqual(len(results), 0)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DRI_Tests ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
