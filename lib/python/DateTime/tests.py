
# To run these tests, use:
#   python unittest.py DateTime.tests.suite

import unittest
from DateTime import DateTime
import string

class DateTimeTests (unittest.TestCase):

    def testBug1203(self):
        '''01:59:60 occurred in old DateTime'''
        dt = DateTime(7200, 'GMT')
        assert string.find(str(dt), '60') < 0, dt

    def testDSTInEffect(self):
        '''Checks GMT offset for a DST date in the US/Eastern time zone'''
        dt = DateTime(2000, 5, 9, 15, 0, 0, 'US/Eastern')
        assert dt.toZone('GMT').hour() == 19, (dt, dt.toZone('GMT'))

    def testDSTNotInEffect(self):
        '''Checks GMT offset for a non-DST date in the US/Eastern time zone'''
        dt = DateTime(2000, 11, 9, 15, 0, 0, 'US/Eastern')
        assert dt.toZone('GMT').hour() == 20, (dt, dt.toZone('GMT'))

    def testAddPrecision(self):
        '''Precision of serial additions'''
        dt = DateTime()
        assert str(dt + 0.10 + 3.14 + 6.76 - 10) == str(dt), dt

    def testConstructor3(self):
        '''Constructor from date/time string'''
        dt = DateTime()
        dt1 = DateTime('%d/%d/%d %d:%d:%f %s' % (
            dt.year(),
            dt.month(),
            dt.day(),
            dt.hour(),
            dt.minute(),
            dt.second(),
            dt.timezone()))
        assert dt.debugCompare(dt1), (dt, dt1)

    def testConstructor4(self):
        '''Constructor from time float'''
        dt = DateTime()
        dt1 = DateTime(float(dt))
        assert dt.debugCompare(dt1), (dt, dt1)

    def testConstructor5(self):
        '''Constructor from time float and timezone'''
        dt = DateTime()
        dt1 = DateTime(float(dt), dt.timezone())
        assert str(dt) == str(dt1), (dt, dt1)

    def testConstructor6(self):
        '''Constructor from year and julian date'''
        dt = DateTime('1980/1/5 12:00:00.050 pm')
        dt1 = DateTime(1980, 5.500000578705)
        assert dt.debugCompare(dt1), (dt, dt1)

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
        assert dt.debugCompare(dt1), (dt, dt1)
        
    def testDayOfWeek(self):
        '''strftime() used to always be passed a day of week of 0.'''
        dt = DateTime('2000/6/16')
        s = dt.strftime('%A')
        assert s == 'Friday', (dt, s)

    def testMultiArgConstructors(self):
        '''Test of constructors 5 and 6'''
        dt = DateTime(957710021.390, DateTime().timezone())
        dt1 = DateTime(2000, 128.440062393519)
        m = dt.millis()
        m1 = dt1.millis()
        assert m == m1, (dt, dt1, m, m1)

    def testOldDate(self):
        '''Fails when an 1800 date is displayed with negative signs'''
        dt = DateTime('1830/5/6 12:31:46.213 pm')
        dt1 = dt.toZone('GMT+6')
        assert string.find(str(dt1), '-') < 0, (dt, dt1)

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
        assert dt1 == dt3, (dt, dt1, dt2, dt3)

    def testTZ1(self):
        '''Time zone manipulation'''
        dt = DateTime('1997/3/9 1:45pm GMT-4')
        dt1 = DateTime('1997/3/9 1:45 am GMT+8')
        assert dt - dt1 == 1.0, (dt, dt1)

    def testTZ2(self):
        '''Time zone manipulation test 2'''
        dt = DateTime()
        dt1 = dt.toZone('GMT')
        s = dt.second()
        s1 = dt1.second()
        assert s == s1, (dt, dt1, s, s1)

    def testY10KDate(self):
        '''Comparison of a Y10K date and a Y2K date'''
        dt = DateTime('10213/09/21')
        dt1 = DateTime(2000, 1, 1)
        assert dt - dt1 == 3000000.0, (dt, dt1)


def suite():
    return unittest.makeSuite(DateTimeTests)
