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
"""DateRangeIndex unit tests.

$Id$
"""

import unittest

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


    def _getTargetClass(self):
        from Products.PluginIndexes.DateRangeIndex.DateRangeIndex \
            import DateRangeIndex
        return DateRangeIndex

    def _makeOne(self,
                 id,
                 since_field=None,
                 until_field=None,
                 caller=None,
                 extra=None,
                ):
        klass = self._getTargetClass()
        return klass(id, since_field, until_field, caller, extra)


    def test_z3interfaces(self):
        from Products.PluginIndexes.interfaces import IDateRangeIndex
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass

        verifyClass(IDateRangeIndex, self._getTargetClass())
        verifyClass(IPluggableIndex, self._getTargetClass())
        verifyClass(ISortIndex, self._getTargetClass())
        verifyClass(IUniqueValueIndex, self._getTargetClass())

    def test_empty( self ):

        empty = self._makeOne( 'empty' )

        assert empty.getEntryForObject( 1234 ) is None
        empty.unindex_object( 1234 ) # shouldn't throw

        assert not empty.uniqueValues( 'foo' )
        assert not empty.uniqueValues( 'foo', 1 )

        assert empty._apply_index( { 'zed' : 12345 } ) is None

        result, used = empty._apply_index( { 'empty' : 12345 } )

        assert not result
        assert used == ( None, None )

    def test_retrieval( self ):

        index = self._makeOne( 'work', 'start', 'stop' )

        for i in range( len( dummies ) ):
            index.index_object( i, dummies[i] )

        for i in range( len( dummies ) ):
            self.assertEqual(index.getEntryForObject( i ), dummies[i].datum())

        for value in range( -1, 15 ):

            matches = matchingDummies( value )
            results, used = index._apply_index( { 'work' : value } )
            assert used == ( 'start', 'stop' )

            assert len( matches ) == len( results ), ( '%s: %s == %s'
               % ( value, map( lambda x: x.name(), matches ), results ) )

            matches.sort( lambda x, y: cmp( x.name(), y.name() ) )

            for result, match in map( None, results, matches ):
                self.assertEqual(index.getEntryForObject(result), match.datum())

    def test_longdates( self ):
        self.assertRaises(OverflowError, self._badlong )

    def _badlong(self):
        import sys
        index = self._makeOne ('work', 'start', 'stop' )
        bad = Dummy( 'bad', long(sys.maxint) + 1, long(sys.maxint) + 1 )
        index.index_object( 0, bad )

    def test_datetime(self):
        from datetime import datetime
        from DateTime.DateTime import DateTime
        from Products.PluginIndexes.DateIndex.tests.test_DateIndex \
            import _getEastern
        before = datetime(2009, 7, 11, 0, 0, tzinfo=_getEastern())
        start = datetime(2009, 7, 13, 5, 15, tzinfo=_getEastern())
        between = datetime(2009, 7, 13, 5, 45, tzinfo=_getEastern())
        stop = datetime(2009, 7, 13, 6, 30, tzinfo=_getEastern())
        after = datetime(2009, 7, 14, 0, 0, tzinfo=_getEastern())

        dummy = Dummy('test', start, stop)
        index = self._makeOne( 'work', 'start', 'stop' )
        index.index_object(0, dummy)

        self.assertEqual(index.getEntryForObject(0),
                        (DateTime(start).millis() / 60000,
                         DateTime(stop).millis() / 60000))

        results, used = index._apply_index( { 'work' : before } )
        self.assertEqual(len(results), 0)

        results, used = index._apply_index( { 'work' : start } )
        self.assertEqual(len(results), 1)

        results, used = index._apply_index( { 'work' : between } )
        self.assertEqual(len(results), 1)

        results, used = index._apply_index( { 'work' : stop } )
        self.assertEqual(len(results), 1)

        results, used = index._apply_index( { 'work' : after } )
        self.assertEqual(len(results), 0)

    def test_datetime_naive_timezone(self):
        from datetime import datetime
        from DateTime.DateTime import DateTime
        from Products.PluginIndexes.DateIndex.DateIndex import Local
        before = datetime(2009, 7, 11, 0, 0)
        start = datetime(2009, 7, 13, 5, 15)
        start_local = datetime(2009, 7, 13, 5, 15, tzinfo=Local)
        between = datetime(2009, 7, 13, 5, 45)
        stop = datetime(2009, 7, 13, 6, 30)
        stop_local = datetime(2009, 7, 13, 6, 30, tzinfo=Local)
        after = datetime(2009, 7, 14, 0, 0)

        dummy = Dummy('test', start, stop)
        index = self._makeOne( 'work', 'start', 'stop' )
        index.index_object(0, dummy)
  
        self.assertEqual(index.getEntryForObject(0),
                        (DateTime(start_local).millis() / 60000,
                         DateTime(stop_local).millis() / 60000))
  
        results, used = index._apply_index( { 'work' : before } )
        self.assertEqual(len(results), 0)

        results, used = index._apply_index( { 'work' : start } )
        self.assertEqual(len(results), 1)

        results, used = index._apply_index( { 'work' : between } )
        self.assertEqual(len(results), 1)

        results, used = index._apply_index( { 'work' : stop } )
        self.assertEqual(len(results), 1)

        results, used = index._apply_index( { 'work' : after } )
        self.assertEqual(len(results), 0)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DRI_Tests ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
