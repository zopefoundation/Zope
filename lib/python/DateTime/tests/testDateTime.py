
# To run these tests, use:
#   python unittest.py DateTime.tests.suite

import math
import os
import time
import unittest

from DateTime.DateTime import _findLocalTimeZoneName
from DateTime import DateTime

try:
    __file__
except NameError:
    import sys
    f = sys.argv[0]
else:
    f = __file__

DATADIR = os.path.dirname(os.path.abspath(f))
del f


class DateTimeTests(unittest.TestCase):

    def _compare(self, dt1, dt2, ms=1):
        '''Compares the internal representation of dt1 with
        the representation in dt2.  Allows sub-millisecond variations.
        Primarily for testing.'''
        if ms:
            self.assertEqual(dt1.millis(), dt2.millis())
        self.assertEqual(math.floor(dt1._t * 1000.0),
                         math.floor(dt2._t * 1000.0))
        self.assertEqual(math.floor(dt1._d * 86400000.0),
                         math.floor(dt2._d * 86400000.0))
        self.assertEqual(math.floor(dt1.time * 86400000.0),
                         math.floor(dt2.time * 86400000.0))

    def testBug1203(self):
        '''01:59:60 occurred in old DateTime'''
        dt = DateTime(7200, 'GMT')
        self.assert_(str(dt).find('60') < 0, dt)

    def testDSTInEffect(self):
        '''Checks GMT offset for a DST date in the US/Eastern time zone'''
        dt = DateTime(2000, 5, 9, 15, 0, 0, 'US/Eastern')
        self.assertEqual(dt.toZone('GMT').hour(), 19,
                         (dt, dt.toZone('GMT')))

    def testDSTNotInEffect(self):
        '''Checks GMT offset for a non-DST date in the US/Eastern time zone'''
        dt = DateTime(2000, 11, 9, 15, 0, 0, 'US/Eastern')
        self.assertEqual(dt.toZone('GMT').hour(), 20,
                         (dt, dt.toZone('GMT')))

    def testAddPrecision(self):
        '''Precision of serial additions'''
        dt = DateTime()
        self.assertEqual(str(dt + 0.10 + 3.14 + 6.76 - 10), str(dt),
                         dt)

    def testConstructor3(self):
        '''Constructor from date/time string'''
        dt = DateTime()
        dt1s = '%d/%d/%d %d:%d:%f %s' % (
            dt.year(),
            dt.month(),
            dt.day(),
            dt.hour(),
            dt.minute(),
            dt.second(),
            dt.timezone())
        dt1 = DateTime(dt1s)
        # Compare representations as it's the
        # only way to compare the dates to the same accuracy
        self.assertEqual(repr(dt),repr(dt1))

    def testConstructor4(self):
        '''Constructor from time float'''
        dt = DateTime()
        dt1 = DateTime(float(dt))
        self._compare(dt,dt1)

    def testConstructor5(self):
        '''Constructor from time float and timezone'''
        dt = DateTime()
        dt1 = DateTime(float(dt), dt.timezone())
        self.assertEqual(str(dt), str(dt1), (dt, dt1))

    def testConstructor6(self):
        '''Constructor from year and julian date'''
        # This test must normalize the time zone, or it *will* break when
        # DST changes!
        dt1 = DateTime(2000, 5.500000578705)
        dt = DateTime('2000/1/5 12:00:00.050 pm %s' % dt1.localZone())
        self._compare(dt, dt1)

    def testConstructor7(self):
        '''Constructor from parts'''
        dt = DateTime()
        dt1 = DateTime(
            dt.year(),
            dt.month(),
            dt.day(),
            dt.hour(),
            dt.minute(),
            dt.second(),
            dt.timezone())
        # Compare representations as it's the
        # only way to compare the dates to the same accuracy
        self.assertEqual(repr(dt), repr(dt1))

    def testDayOfWeek(self):
        '''strftime() used to always be passed a day of week of 0.'''
        dt = DateTime('2000/6/16')
        s = dt.strftime('%A')
        self.assertEqual(s, 'Friday', (dt, s))

    def testOldDate(self):
        '''Fails when an 1800 date is displayed with negative signs'''
        dt = DateTime('1830/5/6 12:31:46.213 pm')
        dt1 = dt.toZone('GMT+6')
        self.assert_(str(dt1).find('-') < 0, (dt, dt1))

    def testSubtraction(self):
        '''Reconstruction of a DateTime from its parts, with subtraction'''
        dt = DateTime()
        dt1 = dt - 3.141592653
        dt2 = DateTime(
            dt.year(),
            dt.month(),
            dt.day(),
            dt.hour(),
            dt.minute(),
            dt.second())
        dt3 = dt2 - 3.141592653
        self.assertEqual(dt1, dt3, (dt, dt1, dt2, dt3))

    def testTZ1add(self):
        '''Time zone manipulation: add to a date'''
        dt = DateTime('1997/3/8 1:45am GMT-4')
        dt1 = DateTime('1997/3/9 1:45pm GMT+8')
        self.assertEqual(dt + 1.0, dt1, (dt, dt1))

    def testTZ1sub(self):
        '''Time zone manipulation: subtract from a date'''
        dt = DateTime('1997/3/8 1:45am GMT-4')
        dt1 = DateTime('1997/3/9 1:45pm GMT+8')
        self.assertEqual(dt1 - 1.0, dt, (dt, dt1))

    def testTZ1diff(self):
        '''Time zone manipulation: diff two dates'''
        dt = DateTime('1997/3/8 1:45am GMT-4')
        dt1 = DateTime('1997/3/9 1:45pm GMT+8')
        self.assertEqual(dt1 - dt, 1.0, (dt, dt1))

    def testCompareMethods(self):
        '''Compare two dates using several methods'''
        dt = DateTime('1997/1/1')
        dt1 = DateTime('1997/2/2')
        self.failUnless(dt1.greaterThan(dt))
        self.failUnless(dt1.greaterThanEqualTo(dt))
        self.failUnless(dt.lessThan(dt1))
        self.failUnless(dt.lessThanEqualTo(dt1))
        self.failUnless(dt.notEqualTo(dt1))
        self.failUnless(not dt.equalTo(dt1))

    def testCompareOperations(self, dt=None, dt1=None):
        """Compare two dates using several operations"""
        if dt is None:
            dt = DateTime('1997/1/1')
        if dt1 is None:
            dt1 = DateTime('1997/2/2')
        self.failUnless(dt1 > dt)
        self.failUnless(dt1 >= dt)
        self.failUnless(dt < dt1)
        self.failUnless(dt <= dt1)
        self.failUnless(dt != dt1)
        self.failUnless(not (dt == dt1))

    def testUpgradeOldInstances(self):
        """Compare dates that don't have the _millis attribute yet."""
        dt = DateTime('1997/1/1')
        dt1 = DateTime('1997/2/2')
        del dt._millis
        del dt1._millis
        self.testCompareOperations(dt, dt1)

    def testTZ2(self):
        '''Time zone manipulation test 2'''
        dt = DateTime()
        dt1 = dt.toZone('GMT')
        s = dt.second()
        s1 = dt1.second()
        self.assertEqual(s, s1, (dt, dt1, s, s1))

    def testTZDiffDaylight(self):
        '''Diff dates across daylight savings dates'''
        dt = DateTime('2000/6/8 1:45am US/Eastern')
        dt1 = DateTime('2000/12/8 12:45am US/Eastern')
        self.assertEqual(dt1 - dt, 183, (dt, dt1, dt1 - dt))

    def testY10KDate(self):
        '''Comparison of a Y10K date and a Y2K date'''
        dt = DateTime('10213/09/21')
        dt1 = DateTime(2000, 1, 1)

        dsec = (dt.millis() - dt1.millis()) / 1000.0
        ddays = math.floor((dsec / 86400.0) + 0.5)

        self.assertEqual(ddays, 3000000L, ddays)

    def test_tzoffset(self):
        '''Test time-zone given as an offset'''

        # GMT
        dt = DateTime('Tue, 10 Sep 2001 09:41:03 GMT')
        self.assertEqual(dt.tzoffset(), 0)

        # Timezone by name, a timezone that hasn't got daylightsaving.
        dt = DateTime('Tue, 2 Mar 2001 09:41:03 GMT+3')
        self.assertEqual(dt.tzoffset(), 10800)

        # Timezone by name, has daylightsaving but is not in effect.
        dt = DateTime('Tue, 21 Jan 2001 09:41:03 PST')
        self.assertEqual(dt.tzoffset(), -28800)

        # Timezone by name, with daylightsaving in effect
        dt = DateTime('Tue, 24 Aug 2001 09:41:03 PST')
        self.assertEqual(dt.tzoffset(), -25200)

        # A negative numerical timezone
        dt = DateTime('Tue, 24 Jul 2001 09:41:03 -0400')
        self.assertEqual(dt.tzoffset(), -14400)

        # A positive numerical timzone
        dt = DateTime('Tue, 6 Dec 1966 01:41:03 +0200')
        self.assertEqual(dt.tzoffset(), 7200)

        # A negative numerical timezone with minutes.
        dt = DateTime('Tue, 24 Jul 2001 09:41:03 -0637')
        self.assertEqual(dt.tzoffset(), -23820)

        # A positive numerical timezone with minutes.
        dt = DateTime('Tue, 24 Jul 2001 09:41:03 +0425')
        self.assertEqual(dt.tzoffset(), 15900)

    def testISO8601(self):
        ''' iso 8601 dates '''

        ref0 = DateTime('2002/5/2 8:00am GMT')
        ref1 = DateTime('2002/5/2 8:00am US/Eastern')

        isoDt = DateTime('2002-05-02T08:00:00')
        self.assertEqual( ref0, isoDt)
        isoDt = DateTime('2002-05-02T08:00:00Z')
        self.assertEqual( ref0, isoDt)

        isoDt = DateTime('2002-05-02T08:00:00-04:00')
        self.assertEqual( ref1, isoDt)

        # Bug 1386: the colon in the timezone offset is optional
        isoDt = DateTime('2002-05-02T08:00:00-0400')
        self.assertEqual( ref1, isoDt)
        
        dgood = '2002-05-02'
        tgood = 'T08:00:00-04:00'
        for dbad in '2002-5-2', '2002-10-2', '2002-2-10', '02-2-10':
            self.assertRaises(DateTime.SyntaxError, DateTime, dbad)
            self.assertRaises(DateTime.SyntaxError, DateTime, dbad + tgood)
        for tbad in '08:00', 'T8:00': #, 'T08:00Z-04:00':
            self.assertRaises(DateTime.SyntaxError, DateTime, dgood + tbad)

        iso8601_string = '2002-05-02T08:00:00-04:00'
        iso8601DT = DateTime(iso8601_string)
        self.assertEqual(iso8601_string, iso8601DT.ISO8601())

    def testJulianWeek(self):
        """ check JulianDayWeek function """

        try:
            import gzip
        except ImportError:
            print "Warning: testJulianWeek disabled: module gzip not found"
            return 0

        fn = os.path.join(DATADIR, 'julian_testdata.txt.gz')
        lines = gzip.GzipFile(fn).readlines()

        for line in lines:
            d = DateTime(line[:10])
            result_from_mx=tuple(map(int, line[12:-2].split(',')))
            self.assertEqual(result_from_mx[1], d.week())

    def testCopyConstructor(self):
        d = DateTime('2004/04/04')
        self.assertEqual(DateTime(d), d)
        self.assertEqual(str(DateTime(d)), str(d))
        d2 = DateTime('1999/04/12 01:00:00')
        self.assertEqual(DateTime(d2), d2)
        self.assertEqual(str(DateTime(d2)), str(d2))

    def testCopyConstructorPreservesTimezone(self):
        # test for https://bugs.launchpad.net/zope2/+bug/200007
        # This always worked in the local timezone, so we need at least
        # two tests with different zones to be sure at least one of them
        # is not local.
        d = DateTime('2004/04/04')
        self.assertEqual(DateTime(d).timezone(), d.timezone())
        d2 = DateTime('2008/04/25 12:00:00 EST')
        self.assertEqual(DateTime(d2).timezone(), d2.timezone())
        self.assertEqual(str(DateTime(d2)), str(d2))
        d3 = DateTime('2008/04/25 12:00:00 PST')
        self.assertEqual(DateTime(d3).timezone(), d3.timezone())
        self.assertEqual(str(DateTime(d3)), str(d3))


    def testRFC822(self):
        '''rfc822 conversion'''
        dt = DateTime('2002-05-02T08:00:00+00:00')
        self.assertEqual(dt.rfc822(), 'Thu, 02 May 2002 08:00:00 +0000')

        dt = DateTime('2002-05-02T08:00:00+02:00')
        self.assertEqual(dt.rfc822(), 'Thu, 02 May 2002 08:00:00 +0200')

        dt = DateTime('2002-05-02T08:00:00-02:00')
        self.assertEqual(dt.rfc822(), 'Thu, 02 May 2002 08:00:00 -0200')

        # Checking that conversion from local time is working.
        dt = DateTime()
        dts = dt.rfc822().split(' ')
        times = dts[4].split(':')
        _isDST = time.localtime(time.time())[8]
        if _isDST: offset = time.altzone
        else:      offset = time.timezone

        self.assertEqual(dts[0], dt.aDay() + ',')
        self.assertEqual(int(dts[1]), dt.day())
        self.assertEqual(dts[2], dt.aMonth())
        self.assertEqual(int(dts[3]), dt.year())
        self.assertEqual(int(times[0]), dt.h_24())
        self.assertEqual(int(times[1]), dt.minute())
        self.assertEqual(int(times[2]), int(dt.second()))
        self.assertEqual(dts[5], "%+03d%02d" % divmod( (-offset/60), 60) )


    def testInternationalDateformat(self):

        for year in range(1990, 2020):
            for month in range (1,13):
                for day in range(1,32):
                    try: d_us = DateTime("%d/%d/%d" % (year,month,day))
                    except: continue

                    d_int = DateTime("%d.%d.%d" % (day,month,year),
                                     datefmt="international")
                    self.assertEqual(d_us, d_int)

                    d_int = DateTime("%d/%d/%d" % (day,month,year),
                                     datefmt="international")
                    self.assertEqual(d_us, d_int)

    def test_calcTimezoneName(self):
        timezone_dependent_epoch = 2177452800L
        try:
            DateTime()._calcTimezoneName(timezone_dependent_epoch, 0)
        except DateTime.TimeError:
            self.fail('Zope Collector issue #484 (negative time bug): '
                      'TimeError raised')
    
    def testStrftimeTZhandling(self):
        '''strftime timezone testing'''
        # This is a test for collector issue #1127
        format = '%Y-%m-%d %H:%M %Z'
        dt = DateTime('Wed, 19 Nov 2003 18:32:07 -0215')
        dt_string = dt.strftime(format)
        dt_local = dt.toZone(_findLocalTimeZoneName(0))
        dt_localstring = dt_local.strftime(format)
        self.assertEqual(dt_string, dt_localstring)

    def testStrftimeFarDates(self):
        '''Checks strftime in dates <= 1900 or >= 2038'''
        dt = DateTime('1900/01/30')
        self.assertEqual(dt.strftime('%d/%m/%Y'), '30/01/1900')
        dt = DateTime('2040/01/30')
        self.assertEqual(dt.strftime('%d/%m/%Y'), '30/01/2040')

    def testZoneInFarDates(self):
        '''Checks time zone in dates <= 1900 or >= 2038'''
        dt1 = DateTime('2040/01/30 14:33 GMT+1')
        dt2 = DateTime('2040/01/30 11:33 GMT-2')
        self.assertEqual(dt1.strftime('%d/%m/%Y %H:%M'),
                         dt2.strftime('%d/%m/%Y %H:%M'))

    def testStrftimeUnicode(self):
        dt = DateTime('2002-05-02T08:00:00+00:00')
        ok = dt.strftime('Le %d/%m/%Y a %Hh%M').replace('a', u'\xe0')
        self.assertEqual(dt.strftime(u'Le %d/%m/%Y \xe0 %Hh%M'), ok)

def test_suite():
    from zope.testing import doctest
    return unittest.TestSuite([
        unittest.makeSuite(DateTimeTests),
        doctest.DocFileSuite('DateTime.txt', package='DateTime')
        ])

if __name__=="__main__":
    unittest.main(defaultTest='test_suite')
