##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Encapsulation of date/time values"""

__version__='$Revision: 1.99 $'[11:-2]


import re, math,  DateTimeZone
from time import time, gmtime, localtime
from time import daylight, timezone, altzone, strftime
from datetime import datetime
from interfaces import IDateTime
from interfaces import DateTimeError, SyntaxError, DateError, TimeError
from zope.interface import implements

default_datefmt = None

def getDefaultDateFormat():
    global default_datefmt
    if default_datefmt is None:
        try:
            from App.config import getConfiguration
            default_datefmt = getConfiguration().datetime_format
            return default_datefmt
        except:
            return 'us'
    else:
        return default_datefmt


try:
    from time import tzname
except:
    tzname=('UNKNOWN','UNKNOWN')

# To control rounding errors, we round system time to the nearest
# millisecond.  Then delicate calculations can rely on that the
# maximum precision that needs to be preserved is known.
_system_time = time
def time():
    return round(_system_time(), 3)

# Determine machine epoch
tm=((0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334),
    (0, 0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335))
yr,mo,dy,hr,mn,sc=gmtime(0)[:6]
i=int(yr-1)
to_year =int(i*365+i/4-i/100+i/400-693960.0)
to_month=tm[yr%4==0 and (yr%100!=0 or yr%400==0)][mo]
EPOCH  =(to_year+to_month+dy+(hr/24.0+mn/1440.0+sc/86400.0))*86400
jd1901 =2415385L

numericTimeZoneMatch=re.compile(r'[+-][0-9][0-9][0-9][0-9]').match #TS

class _timezone:
    def __init__(self,data):
        self.name,self.timect,self.typect, \
        self.ttrans,self.tindex,self.tinfo,self.az=data

    def default_index(self):
        if self.timect == 0: return 0
        for i in range(self.typect):
            if self.tinfo[i][1] == 0: return i
        return 0

    def index(self,t=None):
        t=t or time()
        if self.timect==0: idx=(0, 0, 0)
        elif t < self.ttrans[0]:
            i=self.default_index()
            idx=(i, ord(self.tindex[0]),i)
        elif t >= self.ttrans[-1]:
            if self.timect > 1:
                idx=(ord(self.tindex[-1]),ord(self.tindex[-1]),
                     ord(self.tindex[-2]))
            else:
                idx=(ord(self.tindex[-1]),ord(self.tindex[-1]),
                     self.default_index())
        else:
            for i in range(self.timect-1):
                if t < self.ttrans[i+1]:
                    if i==0: idx=(ord(self.tindex[0]),ord(self.tindex[1]),
                                  self.default_index())
                    else:    idx=(ord(self.tindex[i]),ord(self.tindex[i+1]),
                                  ord(self.tindex[i-1]))
                    break
        return idx

    def info(self,t=None):
        idx=self.index(t)[0]
        zs =self.az[self.tinfo[idx][2]:]
        return self.tinfo[idx][0],self.tinfo[idx][1],zs[:zs.find('\000')]




class _cache:

    _zlst=['Brazil/Acre','Brazil/DeNoronha','Brazil/East',
           'Brazil/West','Canada/Atlantic','Canada/Central',
           'Canada/Eastern','Canada/East-Saskatchewan',
           'Canada/Mountain','Canada/Newfoundland',
           'Canada/Pacific','Canada/Yukon',
           'Chile/Continental','Chile/EasterIsland','CST','Cuba',
           'Egypt','EST','GB-Eire','Greenwich','Hongkong','Iceland',
           'Iran','Israel','Jamaica','Japan','Mexico/BajaNorte',
           'Mexico/BajaSur','Mexico/General','MST','Poland','PST',
           'Singapore','Turkey','Universal','US/Alaska','US/Aleutian',
           'US/Arizona','US/Central','US/Eastern','US/East-Indiana',
           'US/Hawaii','US/Indiana-Starke','US/Michigan',
           'US/Mountain','US/Pacific','US/Samoa','UTC','UCT','GMT',

           'GMT+0100','GMT+0200','GMT+0300','GMT+0400','GMT+0500',
           'GMT+0600','GMT+0700','GMT+0800','GMT+0900','GMT+1000',
           'GMT+1100','GMT+1200','GMT+1300','GMT-0100','GMT-0200',
           'GMT-0300','GMT-0400','GMT-0500','GMT-0600','GMT-0700',
           'GMT-0800','GMT-0900','GMT-1000','GMT-1100','GMT-1200',
           'GMT+1',

           'GMT+0130', 'GMT+0230', 'GMT+0330', 'GMT+0430', 'GMT+0530',
           'GMT+0630', 'GMT+0730', 'GMT+0830', 'GMT+0930', 'GMT+1030',
           'GMT+1130', 'GMT+1230',

           'GMT-0130', 'GMT-0230', 'GMT-0330', 'GMT-0430', 'GMT-0530',
           'GMT-0630', 'GMT-0730', 'GMT-0830', 'GMT-0930', 'GMT-1030',
           'GMT-1130', 'GMT-1230',

           'UT','BST','MEST','SST','FST','WADT','EADT','NZDT',
           'WET','WAT','AT','AST','NT','IDLW','CET','MET',
           'MEWT','SWT','FWT','EET','EEST','BT','ZP4','ZP5','ZP6',
           'WAST','CCT','JST','EAST','GST','NZT','NZST','IDLE']


    _zmap={'aest':'GMT+1000', 'aedt':'GMT+1100',
           'aus eastern standard time':'GMT+1000',
           'sydney standard time':'GMT+1000',
           'tasmania standard time':'GMT+1000',
           'e. australia standard time':'GMT+1000',
           'aus central standard time':'GMT+0930',
           'cen. australia standard time':'GMT+0930',
           'w. australia standard time':'GMT+0800',

           'brazil/acre':'Brazil/Acre',
           'brazil/denoronha':'Brazil/Denoronha',
           'brazil/east':'Brazil/East','brazil/west':'Brazil/West',
           'canada/atlantic':'Canada/Atlantic',
           'canada/central':'Canada/Central',
           'canada/eastern':'Canada/Eastern',
           'canada/east-saskatchewan':'Canada/East-Saskatchewan',
           'canada/mountain':'Canada/Mountain',
           'canada/newfoundland':'Canada/Newfoundland',
           'canada/pacific':'Canada/Pacific','canada/yukon':'Canada/Yukon',
           'central europe standard time':'GMT+0100',
           'chile/continental':'Chile/Continental',
           'chile/easterisland':'Chile/EasterIsland',
           'cst':'US/Central','cuba':'Cuba','est':'US/Eastern','egypt':'Egypt',
           'eastern standard time':'US/Eastern',
           'us eastern standard time':'US/Eastern',
           'central standard time':'US/Central',
           'mountain standard time':'US/Mountain',
           'pacific standard time':'US/Pacific',
           'gb-eire':'GB-Eire','gmt':'GMT',

           'gmt+0000':'GMT+0', 'gmt+0':'GMT+0',


           'gmt+0100':'GMT+1', 'gmt+0200':'GMT+2', 'gmt+0300':'GMT+3',
           'gmt+0400':'GMT+4', 'gmt+0500':'GMT+5', 'gmt+0600':'GMT+6',
           'gmt+0700':'GMT+7', 'gmt+0800':'GMT+8', 'gmt+0900':'GMT+9',
           'gmt+1000':'GMT+10','gmt+1100':'GMT+11','gmt+1200':'GMT+12',
           'gmt+1300':'GMT+13',
           'gmt-0100':'GMT-1', 'gmt-0200':'GMT-2', 'gmt-0300':'GMT-3',
           'gmt-0400':'GMT-4', 'gmt-0500':'GMT-5', 'gmt-0600':'GMT-6',
           'gmt-0700':'GMT-7', 'gmt-0800':'GMT-8', 'gmt-0900':'GMT-9',
           'gmt-1000':'GMT-10','gmt-1100':'GMT-11','gmt-1200':'GMT-12',

           'gmt+1': 'GMT+1', 'gmt+2': 'GMT+2', 'gmt+3': 'GMT+3',
           'gmt+4': 'GMT+4', 'gmt+5': 'GMT+5', 'gmt+6': 'GMT+6',
           'gmt+7': 'GMT+7', 'gmt+8': 'GMT+8', 'gmt+9': 'GMT+9',
           'gmt+10':'GMT+10','gmt+11':'GMT+11','gmt+12':'GMT+12',
           'gmt+13':'GMT+13',
           'gmt-1': 'GMT-1', 'gmt-2': 'GMT-2', 'gmt-3': 'GMT-3',
           'gmt-4': 'GMT-4', 'gmt-5': 'GMT-5', 'gmt-6': 'GMT-6',
           'gmt-7': 'GMT-7', 'gmt-8': 'GMT-8', 'gmt-9': 'GMT-9',
           'gmt-10':'GMT-10','gmt-11':'GMT-11','gmt-12':'GMT-12',

           'gmt+130':'GMT+0130',  'gmt+0130':'GMT+0130',
           'gmt+230':'GMT+0230',  'gmt+0230':'GMT+0230',
           'gmt+330':'GMT+0330',  'gmt+0330':'GMT+0330',
           'gmt+430':'GMT+0430',  'gmt+0430':'GMT+0430',
           'gmt+530':'GMT+0530',  'gmt+0530':'GMT+0530',
           'gmt+630':'GMT+0630',  'gmt+0630':'GMT+0630',
           'gmt+730':'GMT+0730',  'gmt+0730':'GMT+0730',
           'gmt+830':'GMT+0830',  'gmt+0830':'GMT+0830',
           'gmt+930':'GMT+0930',  'gmt+0930':'GMT+0930',
           'gmt+1030':'GMT+1030',
           'gmt+1130':'GMT+1130',
           'gmt+1230':'GMT+1230',

           'gmt-130':'GMT-0130',  'gmt-0130':'GMT-0130',
           'gmt-230':'GMT-0230',  'gmt-0230':'GMT-0230',
           'gmt-330':'GMT-0330',  'gmt-0330':'GMT-0330',
           'gmt-430':'GMT-0430',  'gmt-0430':'GMT-0430',
           'gmt-530':'GMT-0530',  'gmt-0530':'GMT-0530',
           'gmt-630':'GMT-0630',  'gmt-0630':'GMT-0630',
           'gmt-730':'GMT-0730',  'gmt-0730':'GMT-0730',
           'gmt-830':'GMT-0830',  'gmt-0830':'GMT-0830',
           'gmt-930':'GMT-0930',  'gmt-0930':'GMT-0930',
           'gmt-1030':'GMT-1030',
           'gmt-1130':'GMT-1130',
           'gmt-1230':'GMT-1230',

           'greenwich':'Greenwich','hongkong':'Hongkong',
           'iceland':'Iceland','iran':'Iran','israel':'Israel',
           'jamaica':'Jamaica','japan':'Japan',
           'mexico/bajanorte':'Mexico/BajaNorte',
           'mexico/bajasur':'Mexico/BajaSur','mexico/general':'Mexico/General',
           'mst':'US/Mountain','pst':'US/Pacific','poland':'Poland',
           'singapore':'Singapore','turkey':'Turkey','universal':'Universal',
           'utc':'Universal','uct':'Universal','us/alaska':'US/Alaska',
           'us/aleutian':'US/Aleutian','us/arizona':'US/Arizona',
           'us/central':'US/Central','us/eastern':'US/Eastern',
           'us/east-indiana':'US/East-Indiana','us/hawaii':'US/Hawaii',
           'us/indiana-starke':'US/Indiana-Starke','us/michigan':'US/Michigan',
           'us/mountain':'US/Mountain','us/pacific':'US/Pacific',
           'us/samoa':'US/Samoa',

           'ut':'Universal',
           'bst':'GMT+1', 'mest':'GMT+2', 'sst':'GMT+2',
           'fst':'GMT+2', 'wadt':'GMT+8', 'eadt':'GMT+11', 'nzdt':'GMT+13',
           'wet':'GMT', 'wat':'GMT-1', 'at':'GMT-2', 'ast':'GMT-4',
           'nt':'GMT-11', 'idlw':'GMT-12', 'cet':'GMT+1', 'cest':'GMT+2',
           'met':'GMT+1',
           'mewt':'GMT+1', 'swt':'GMT+1', 'fwt':'GMT+1', 'eet':'GMT+2',
           'eest':'GMT+3',
           'bt':'GMT+3', 'zp4':'GMT+4', 'zp5':'GMT+5', 'zp6':'GMT+6',
           'wast':'GMT+7', 'cct':'GMT+8', 'jst':'GMT+9', 'east':'GMT+10',
           'gst':'GMT+10', 'nzt':'GMT+12', 'nzst':'GMT+12', 'idle':'GMT+12',
           'ret':'GMT+4', 'ist': 'GMT+0530'
           }

    def __init__(self):
        self._db=DateTimeZone._data
        self._d,self._zidx={},self._zmap.keys()

    def __getitem__(self,k):
        try:   n=self._zmap[k.lower()]
        except KeyError:
            if numericTimeZoneMatch(k) == None:
                raise DateTimeError,'Unrecognized timezone: %s' % k
            return k
        try: return self._d[n]
        except KeyError:
            z=self._d[n]=_timezone(self._db[n])
            return z



def _findLocalTimeZoneName(isDST):
    if not daylight:
        # Daylight savings does not occur in this time zone.
        isDST = 0
    try:
        # Get the name of the current time zone depending
        # on DST.
        _localzone = _cache._zmap[tzname[isDST].lower()]
    except:
        try:
            # Generate a GMT-offset zone name.
            if isDST:
                localzone = altzone
            else:
                localzone = timezone
            offset=(-localzone/(60*60.0))
            majorOffset=int(offset)
            if majorOffset != 0 :
                minorOffset=abs(int((offset % majorOffset) * 60.0))
            else: minorOffset = 0
            m=majorOffset >= 0 and '+' or ''
            lz='%s%0.02d%0.02d' % (m, majorOffset, minorOffset)
            _localzone = _cache._zmap[('GMT%s' % lz).lower()]
        except:
            _localzone = ''
    return _localzone

# Some utility functions for calculating dates:

def _calcSD(t):
    # Returns timezone-independent days since epoch and the fractional
    # part of the days.
    dd = t + EPOCH - 86400.0
    d = dd / 86400.0
    s = d - math.floor(d)
    return s, d

def _calcDependentSecond(tz, t):
    # Calculates the timezone-dependent second (integer part only)
    # from the timezone-independent second.
    fset = _tzoffset(tz, t)
    return fset + long(math.floor(t)) + long(EPOCH) - 86400L

def _calcDependentSecond2(yr,mo,dy,hr,mn,sc):
    # Calculates the timezone-dependent second (integer part only)
    # from the date given.
    ss = int(hr) * 3600 + int(mn) * 60 + int(sc)
    x = long(_julianday(yr,mo,dy)-jd1901) * 86400 + ss
    return x

def _calcIndependentSecondEtc(tz, x, ms):
    # Derive the timezone-independent second from the timezone
    # dependent second.
    fsetAtEpoch = _tzoffset(tz, 0.0)
    nearTime = x - fsetAtEpoch - long(EPOCH) + 86400L + ms
    # nearTime is now within an hour of being correct.
    # Recalculate t according to DST.
    fset = long(_tzoffset(tz, nearTime))
    x_adjusted = x - fset + ms
    d = x_adjusted / 86400.0
    t = x_adjusted - long(EPOCH) + 86400L
    millis = (x + 86400 - fset) * 1000 + \
             long(round(ms * 1000.0)) - long(EPOCH * 1000.0)
    s = d - math.floor(d)
    return s,d,t,millis

def _calcHMS(x, ms):
    # hours, minutes, seconds from integer and float.
    hr = x / 3600
    x = x - hr * 3600
    mn = x / 60
    sc = x - mn * 60 + ms
    return hr,mn,sc

def _calcYMDHMS(x, ms):
    # x is a timezone-dependent integer of seconds.
    # Produces yr,mo,dy,hr,mn,sc.
    yr,mo,dy=_calendarday(x / 86400 + jd1901)
    x = int(x - (x / 86400) * 86400)
    hr = x / 3600
    x = x - hr * 3600
    mn = x / 60
    sc = x - mn * 60 + ms
    return yr,mo,dy,hr,mn,sc

def _julianday(yr,mo,dy):
    y,m,d=long(yr),long(mo),long(dy)
    if m > 12L:
        y=y+m/12L
        m=m%12L
    elif m < 1L:
        m=-m
        y=y-m/12L-1L
        m=12L-m%12L
    if y > 0L: yr_correct=0L
    else:      yr_correct=3L
    if m < 3L: y, m=y-1L,m+12L
    if y*10000L+m*100L+d > 15821014L: b=2L-y/100L+y/400L
    else: b=0L
    return (1461L*y-yr_correct)/4L+306001L*(m+1L)/10000L+d+1720994L+b

def _calendarday(j):
    j=long(j)
    if(j < 2299160L):
        b=j+1525L
    else:
        a=(4L*j-7468861L)/146097L
        b=j+1526L+a-a/4L
    c=(20L*b-2442L)/7305L
    d=1461L*c/4L
    e=10000L*(b-d)/306001L
    dy=int(b-d-306001L*e/10000L)
    mo=(e < 14L) and int(e-1L) or int(e-13L)
    yr=(mo > 2) and (c-4716L) or (c-4715L)
    return int(yr),int(mo),int(dy)

def _tzoffset(tz, t):
    """Returns the offset in seconds to GMT from a specific timezone (tz) at 
    a specific time (t).  NB! The _tzoffset result is the same same sign as 
    the time zone, i.e. GMT+2 has a 7200 second offset. This is the opposite 
    sign of time.timezone which (confusingly) is -7200 for GMT+2."""
    try:
        return DateTime._tzinfo[tz].info(t)[0]
    except:
        if numericTimeZoneMatch(tz) is not None:
            return int(tz[0:3])*3600+int(tz[0]+tz[3:5])*60
        else:
            return 0 # ??

def _correctYear(year):
    # Y2K patch.
    if year >= 0 and year < 100:
        # 00-69 means 2000-2069, 70-99 means 1970-1999.
        if year < 70:
            year = 2000 + year
        else:
            year = 1900 + year
    return year

def safegmtime(t):
    '''gmtime with a safety zone.'''
    try:
        t_int = int(t)
        if isinstance(t_int, long):
            raise OverflowError # Python 2.3 fix: int can return a long!
        return gmtime(t_int)
    except (ValueError, OverflowError):
        raise TimeError, 'The time %f is beyond the range ' \
              'of this Python implementation.' % float(t)

def safelocaltime(t):
    '''localtime with a safety zone.'''
    try:
        t_int = int(t)
        if isinstance(t_int, long):
            raise OverflowError # Python 2.3 fix: int can return a long!
        return localtime(t_int)
    except (ValueError, OverflowError):
        raise TimeError, 'The time %f is beyond the range ' \
              'of this Python implementation.' % float(t)

def _tzoffset2rfc822zone(seconds):
    """Takes an offset, such as from _tzoffset(), and returns an rfc822 
       compliant zone specification. Please note that the result of 
       _tzoffset() is the negative of what time.localzone and time.altzone is."""
    return "%+03d%02d" % divmod( (seconds/60), 60) 

def _tzoffset2iso8601zone(seconds):
    """Takes an offset, such as from _tzoffset(), and returns an ISO 8601
       compliant zone specification. Please note that the result of
       _tzoffset() is the negative of what time.localzone and time.altzone is."""
    return "%+03d:%02d" % divmod( (seconds/60), 60)


class DateTime:
    """DateTime objects represent instants in time and provide
       interfaces for controlling its representation without
       affecting the absolute value of the object.

       DateTime objects may be created from a wide variety of string
       or numeric data, or may be computed from other DateTime objects.
       DateTimes support the ability to convert their representations
       to many major timezones, as well as the ablility to create a
       DateTime object in the context of a given timezone.

       DateTime objects provide partial numerical behavior:

          - Two date-time objects can be subtracted to obtain a time,
            in days between the two.

          - A date-time object and a positive or negative number may
            be added to obtain a new date-time object that is the given
            number of days later than the input date-time object.

          - A positive or negative number and a date-time object may
            be added to obtain a new date-time object that is the given
            number of days later than the input date-time object.

          - A positive or negative number may be subtracted from a
            date-time object to obtain a new date-time object that is
            the given number of days earlier than the input date-time
            object.

        DateTime objects may be converted to integer, long, or float
        numbers of days since January 1, 1901, using the standard int,
        long, and float functions (Compatibility Note: int, long and
        float return the number of days since 1901 in GMT rather than
        local machine timezone). DateTime objects also provide access
        to their value in a float format usable with the python time
        module, provided that the value of the object falls in the
        range of the epoch-based time module.

        A DateTime object should be considered immutable; all conversion
        and numeric operations return a new DateTime object rather than
        modify the current object."""

    implements(IDateTime)

    # For security machinery:
    __roles__=None
    __allow_access_to_unprotected_subobjects__=1

    # Make class-specific exceptions available as attributes.
    DateError = DateError
    TimeError = TimeError
    DateTimeError = DateTimeError
    SyntaxError = SyntaxError

    def __init__(self,*args, **kw):
        """Return a new date-time object"""

        try:
            return self._parse_args(*args, **kw)
        except (DateError, TimeError, DateTimeError):
            raise
        except:
            raise SyntaxError('Unable to parse %s, %s' % (args, kw))


    def _parse_args(self, *args, **kw):
        """Return a new date-time object

        A DateTime object always maintains its value as an absolute
        UTC time, and is represented in the context of some timezone
        based on the arguments used to create the object. A DateTime
        object's methods return values based on the timezone context.

        Note that in all cases the local machine timezone is used for
        representation if no timezone is specified.

        DateTimes may be created with from zero to seven arguments.


          - If the function is called with no arguments or with None, 
            then the current date/time is returned, represented in the
            timezone of the local machine. 

          - If the function is invoked with a single string argument
            which is a recognized timezone name, an object representing
            the current time is returned, represented in the specified
            timezone.

          - If the function is invoked with a single string argument
            representing a valid date/time, an object representing
            that date/time will be returned.

            As a general rule, any date-time representation that is
            recognized and unambigous to a resident of North America is
            acceptable.(The reason for this qualification is that
            in North America, a date like: 2/1/1994 is interpreted
            as February 1, 1994, while in some parts of the world,
            it is interpreted as January 2, 1994.) A date/time
            string consists of two components, a date component and
            an optional time component, separated by one or more
            spaces. If the time component is omited, 12:00am is
            assumed. Any recognized timezone name specified as the
            final element of the date/time string will be used for
            computing the date/time value. (If you create a DateTime
            with the string 'Mar 9, 1997 1:45pm US/Pacific', the
            value will essentially be the same as if you had captured
            time.time() at the specified date and time on a machine in
            that timezone)
            <PRE>

            e=DateTime('US/Eastern')
            # returns current date/time, represented in US/Eastern.

            x=DateTime('1997/3/9 1:45pm')
            # returns specified time, represented in local machine zone.

            y=DateTime('Mar 9, 1997 13:45:00')
            # y is equal to x


            </PRE>

            New in Zope 2.4:
            The DateTime constructor automatically detects and handles
            ISO8601 compliant dates (YYYY-MM-DDThh:ss:mmTZD).
            See http://www.w3.org/TR/NOTE-datetime for full specs.

            The date component consists of year, month, and day
            values. The year value must be a one-, two-, or
            four-digit integer. If a one- or two-digit year is
            used, the year is assumed to be in the twentieth
            century. The month may an integer, from 1 to 12, a
            month name, or a month abreviation, where a period may
            optionally follow the abreviation. The day must be an
            integer from 1 to the number of days in the month. The
            year, month, and day values may be separated by
            periods, hyphens, forward, shashes, or spaces. Extra
            spaces are permitted around the delimiters. Year,
            month, and day values may be given in any order as long
            as it is possible to distinguish the components. If all
            three components are numbers that are less than 13,
            then a a month-day-year ordering is assumed.

            The time component consists of hour, minute, and second
            values separated by colons.  The hour value must be an
            integer between 0 and 23 inclusively. The minute value
            must be an integer between 0 and 59 inclusively. The
            second value may be an integer value between 0 and
            59.999 inclusively. The second value or both the minute
            and second values may be ommitted. The time may be
            followed by am or pm in upper or lower case, in which
            case a 12-hour clock is assumed.

          - If the DateTime function is invoked with a single
            Numeric argument, the number is assumed to be
            a floating point value such as that returned by
            time.time().

            A DateTime object is returned that represents
            the gmt value of the time.time() float represented in
            the local machine's timezone.

          - If the DateTime function is invoked with a single
            argument that is a DateTime instane, a copy of the 
            passed object will be created.

          - If the function is invoked with two numeric arguments,
            then the first is taken to be an integer year and the
            second argument is taken to be an offset in days from
            the beginning of the year, in the context of the local
            machine timezone.
            The date-time value returned is the given offset number of
            days from the beginning of the given year, represented in
            the timezone of the local machine. The offset may be positive
            or negative.
            Two-digit years are assumed to be in the twentieth
            century.

          - If the function is invoked with two arguments, the first
            a float representing a number of seconds past the epoch
            in gmt (such as those returned by time.time()) and the
            second a string naming a recognized timezone, a DateTime
            with a value of that gmt time will be returned, represented
            in the given timezone.
            <PRE>
            import time
            t=time.time()

            now_east=DateTime(t,'US/Eastern')
            # Time t represented as US/Eastern

            now_west=DateTime(t,'US/Pacific')
            # Time t represented as US/Pacific

            # now_east == now_west
            # only their representations are different

            </PRE>

          - If the function is invoked with three or more numeric
            arguments, then the first is taken to be an integer
            year, the second is taken to be an integer month, and
            the third is taken to be an integer day. If the
            combination of values is not valid, then a
            DateError is raised. Two-digit years are assumed
            to be in the twentieth century. The fourth, fifth, and
            sixth arguments specify a time in hours, minutes, and
            seconds; hours and minutes should be positive integers
            and seconds is a positive floating point value, all of
            these default to zero if not given. An optional string may
            be given as the final argument to indicate timezone (the
            effect of this is as if you had taken the value of time.time()
            at that time on a machine in the specified timezone).

            New in Zope 2.7:
            A new keyword parameter "datefmt" can be passed to the 
            constructor. If set to "international", the constructor
            is forced to treat ambigious dates as "days before month
            before year". This useful if you need to parse non-US
            dates in a reliable way

        In any case that a floating point number of seconds is given
        or derived, it's rounded to the nearest millisecond.

        If a string argument passed to the DateTime constructor cannot be
        parsed, it will raise DateTime.SyntaxError. Invalid date components
        will raise a DateError, while invalid time or timezone components
        will raise a DateTimeError.

        The module function Timezones() will return a list of the
        timezones recognized by the DateTime module. Recognition of
        timezone names is case-insensitive.""" #'

        datefmt = kw.get('datefmt', getDefaultDateFormat())
        d=t=s=None
        ac=len(args)
        millisecs = None

        if ac==10:
            # Internal format called only by DateTime
            yr,mo,dy,hr,mn,sc,tz,t,d,s=args                  
        elif ac == 11:
            # Internal format that includes milliseconds.
            yr,mo,dy,hr,mn,sc,tz,t,d,s,millisecs=args

        elif not args or (ac and args[0]==None):
            # Current time, to be displayed in local timezone
            t = time()
            lt = safelocaltime(t)
            tz = self.localZone(lt)
            ms = (t - math.floor(t))
            s,d = _calcSD(t)
            yr,mo,dy,hr,mn,sc=lt[:6]
            sc=sc+ms

        elif ac==1:
            arg=args[0]

            if arg=='':
                raise SyntaxError, arg

            if isinstance(arg, DateTime):
                """ Construct a new DateTime instance from a given DateTime instance """
                t = arg.timeTime()
                lt = safelocaltime(t)
                tz = self.localZone(lt)
                ms = (t - math.floor(t))
                s,d = _calcSD(t)
                yr,mo,dy,hr,mn,sc=lt[:6]
                sc=sc+ms

            elif isinstance(arg, (unicode, str)) and arg.lower() in self._tzinfo._zidx:
                # Current time, to be displayed in specified timezone
                t,tz=time(),self._tzinfo._zmap[arg.lower()]
                ms=(t-math.floor(t))
                # Use integer arithmetic as much as possible.
                s,d = _calcSD(t)
                x = _calcDependentSecond(tz, t)
                yr,mo,dy,hr,mn,sc = _calcYMDHMS(x, ms)

            elif isinstance(arg, (unicode, str)):
                # Date/time string

                if arg.find(' ')==-1 and arg[4]=='-':
                    yr,mo,dy,hr,mn,sc,tz=self._parse_iso8601(arg)
                else:
                    yr,mo,dy,hr,mn,sc,tz=self._parse(arg, datefmt)


                if not self._validDate(yr,mo,dy):
                    raise DateError, 'Invalid date: %s' % arg
                if not self._validTime(hr,mn,int(sc)):
                    raise TimeError, 'Invalid time: %s' % arg
                ms = sc - math.floor(sc)
                x = _calcDependentSecond2(yr,mo,dy,hr,mn,sc)

                if tz:
                    try: tz=self._tzinfo._zmap[tz.lower()]
                    except KeyError:
                        if numericTimeZoneMatch(tz) is None:
                            raise DateTimeError, \
                                  'Unknown time zone in date: %s' % arg
                else:
                    tz = self._calcTimezoneName(x, ms)
                s,d,t,millisecs = _calcIndependentSecondEtc(tz, x, ms)

            else:
                # Seconds from epoch, gmt
                t = arg
                lt = safelocaltime(t)
                tz = self.localZone(lt)
                ms=(t-math.floor(t))
                s,d = _calcSD(t)
                yr,mo,dy,hr,mn,sc=lt[:6]
                sc=sc+ms

        elif ac==2:
            if isinstance(args[1], str):
                # Seconds from epoch (gmt) and timezone
                t,tz=args
                ms = (t - math.floor(t))
                tz=self._tzinfo._zmap[tz.lower()]
                # Use integer arithmetic as much as possible.
                s,d = _calcSD(t)
                x = _calcDependentSecond(tz, t)
                yr,mo,dy,hr,mn,sc = _calcYMDHMS(x, ms)
            else:
                # Year, julian expressed in local zone
                t = time()
                lt = safelocaltime(t)
                tz = self.localZone(lt)
                yr,jul=args
                yr = _correctYear(yr)
                d=(_julianday(yr,1,0)-jd1901)+jul
                x_float = d * 86400.0
                x_floor = math.floor(x_float)
                ms = x_float - x_floor
                x = long(x_floor)
                yr,mo,dy,hr,mn,sc = _calcYMDHMS(x, ms)
                s,d,t,millisecs = _calcIndependentSecondEtc(tz, x, ms)
        else:
            # Explicit format
            yr,mo,dy=args[:3]
            hr,mn,sc,tz=0,0,0,0
            yr = _correctYear(yr)
            if not self._validDate(yr,mo,dy):
                raise DateError, 'Invalid date: %s' % (args,)
            args=args[3:]
            if args:
                hr,args=args[0],args[1:]
                if args:
                    mn,args=args[0],args[1:]
                    if args:
                        sc,args=args[0],args[1:]
                        if args:
                            tz,args=args[0],args[1:]
                            if args:
                                raise DateTimeError,'Too many arguments'
            if not self._validTime(hr,mn,sc):
                raise TimeError, 'Invalid time: %s' % `args`
            leap = (yr % 4 == 0) and (yr % 100 != 0 or yr % 400 == 0)

            x = _calcDependentSecond2(yr,mo,dy,hr,mn,sc)
            ms = sc - math.floor(sc)
            if tz:
                try: tz=self._tzinfo._zmap[tz.lower()]
                except KeyError:
                    if numericTimeZoneMatch(tz) is None:
                        raise DateTimeError, \
                              'Unknown time zone: %s' % tz
            else:
                # Get local time zone name
                tz = self._calcTimezoneName(x, ms)
            s,d,t,millisecs = _calcIndependentSecondEtc(tz, x, ms)

        if hr>12:
            self._pmhour=hr-12
            self._pm='pm'
        else:
            self._pmhour=hr or 12
            self._pm= (hr==12) and 'pm' or 'am'
        self._dayoffset=dx=int((_julianday(yr,mo,dy)+2L)%7)
        self._fmon,self._amon,self._pmon= \
            self._months[mo],self._months_a[mo],self._months_p[mo]
        self._fday,self._aday,self._pday= \
            self._days[dx],self._days_a[dx],self._days_p[dx]
        # Round to nearest millisecond in platform-independent way.  You
        # cannot rely on C sprintf (Python '%') formatting to round
        # consistently; doing it ourselves ensures that all but truly
        # horrid C sprintf implementations will yield the same result
        # x-platform, provided the format asks for exactly 3 digits after
        # the decimal point.
        sc = round(sc, 3)
        if sc >= 60.0:  # can happen if, e.g., orig sc was 59.9999
            sc = 59.999
        self._nearsec=math.floor(sc)
        self._year,self._month,self._day     =yr,mo,dy
        self._hour,self._minute,self._second =hr,mn,sc
        self.time,self._d,self._t,self._tz   =s,d,t,tz
        if millisecs is None:
            millisecs = long(math.floor(t * 1000.0))
        self._millis = millisecs
        # self._millis is the time since the epoch
        # in long integer milliseconds.

    int_pattern  =re.compile(r'([0-9]+)') #AJ
    flt_pattern  =re.compile(r':([0-9]+\.[0-9]+)') #AJ
    name_pattern =re.compile(r'([a-zA-Z]+)', re.I) #AJ
    space_chars  =' \t\n'
    delimiters   ='-/.:,+'
    _month_len  =((0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31),
                  (0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31))
    _until_month=((0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334),
                  (0, 0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335))
    _months     =['','January','February','March','April','May','June','July',
                     'August', 'September', 'October', 'November', 'December']
    _months_a   =['','Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    _months_p   =['','Jan.', 'Feb.', 'Mar.', 'Apr.', 'May', 'June',
                     'July', 'Aug.', 'Sep.', 'Oct.', 'Nov.', 'Dec.']
    _monthmap   ={'january': 1,   'jan': 1,
                  'february': 2,  'feb': 2,
                  'march': 3,     'mar': 3,
                  'april': 4,     'apr': 4,
                  'may': 5,
                  'june': 6,      'jun': 6,
                  'july': 7,      'jul': 7,
                  'august': 8,    'aug': 8,
                  'september': 9, 'sep': 9, 'sept': 9,
                  'october': 10,  'oct': 10,
                  'november': 11, 'nov': 11,
                  'december': 12, 'dec': 12}
    _days       =['Sunday','Monday','Tuesday','Wednesday',
                  'Thursday','Friday','Saturday']
    _days_a     =['Sun',  'Mon',  'Tue',  'Wed',  'Thu',  'Fri',  'Sat' ]
    _days_p     =['Sun.', 'Mon.', 'Tue.', 'Wed.', 'Thu.', 'Fri.', 'Sat.']
    _daymap     ={'sunday': 1,    'sun': 1,
                  'monday': 2,    'mon': 2,
                  'tuesday': 3,   'tues': 3,  'tue': 3,
                  'wednesday': 4, 'wed': 4,
                  'thursday': 5,  'thurs': 5, 'thur': 5, 'thu': 5,
                  'friday': 6,    'fri': 6,
                  'saturday': 7,  'sat': 7}

    _localzone0 = _findLocalTimeZoneName(0)
    _localzone1 = _findLocalTimeZoneName(1)
    _multipleZones = (_localzone0 != _localzone1)
    # For backward compatibility only:
    _isDST = localtime(time())[8]
    _localzone  = _isDST and _localzone1 or _localzone0

    _tzinfo     = _cache()

    def localZone(self, ltm=None):
        '''Returns the time zone on the given date.  The time zone
        can change according to daylight savings.'''
        if not DateTime._multipleZones:
            return DateTime._localzone0
        if ltm == None:
            ltm = localtime(time())
        isDST = ltm[8]
        lz = isDST and DateTime._localzone1 or DateTime._localzone0
        return lz

    def _calcTimezoneName(self, x, ms):
        # Derive the name of the local time zone at the given
        # timezone-dependent second.
        if not DateTime._multipleZones:
            return DateTime._localzone0
        fsetAtEpoch = _tzoffset(DateTime._localzone0, 0.0)
        nearTime = x - fsetAtEpoch - long(EPOCH) + 86400L + ms
        # nearTime is within an hour of being correct.
        try:
            ltm = safelocaltime(nearTime)
        except:
            # We are beyond the range of Python's date support.
            # Hopefully we can assume that daylight savings schedules
            # repeat every 28 years.  Calculate the name of the
            # time zone using a supported range of years.
            yr,mo,dy,hr,mn,sc = _calcYMDHMS(x, 0)
            yr = ((yr - 1970) % 28) + 1970
            x = _calcDependentSecond2(yr,mo,dy,hr,mn,sc)
            nearTime = x - fsetAtEpoch - long(EPOCH) + 86400L + ms

            # nearTime might still be negative if we are east of Greenwich.
            # But we can asume on 1969/12/31 were no timezone changes.
            nearTime = max(0, nearTime)

            ltm = safelocaltime(nearTime)
        tz = self.localZone(ltm)
        return tz

    def _parse(self,st, datefmt=getDefaultDateFormat()):
        # Parse date-time components from a string
        month=year=tz=tm=None
        spaces        =self.space_chars
        intpat        =self.int_pattern
        fltpat        =self.flt_pattern
        wordpat       =self.name_pattern
        delimiters    =self.delimiters
        MonthNumbers  =self._monthmap
        DayOfWeekNames=self._daymap
        ValidZones    =self._tzinfo._zidx
        TimeModifiers =['am','pm']

        # Find timezone first, since it should always be the last
        # element, and may contain a slash, confusing the parser.
        st= st.strip()
        sp=st.split()
        tz=sp[-1]
        if tz and (tz.lower() in ValidZones): st=' '.join(sp[:-1])
        else: tz = None  # Decide later, since the default time zone
        # could depend on the date.

        ints,dels=[],[]
        i,l=0,len(st)
        while i < l:
            while i < l and st[i] in spaces    : i=i+1
            if i < l and st[i] in delimiters:
                d=st[i]
                i=i+1
            else: d=''
            while i < l and st[i] in spaces    : i=i+1

            # The float pattern needs to look back 1 character, because it
            # actually looks for a preceding colon like ':33.33'. This is
            # needed to avoid accidentally matching the date part of a
            # dot-separated date string such as '1999.12.31'.
            if i > 0: b=i-1
            else: b=i

            ts_results = fltpat.match(st, b)
            if ts_results:
                s=ts_results.group(1)
                i=i+len(s)
                ints.append(float(s))
                continue

            #AJ
            ts_results = intpat.match(st, i)
            if ts_results:
                s=ts_results.group(0)

                ls=len(s)
                i=i+ls
                if (ls==4 and d and d in '+-' and
                    (len(ints) + (not not month) >= 3)):
                    tz='%s%s' % (d,s)
                else:
                    v=int(s)
                    ints.append(v)
                continue


            ts_results = wordpat.match(st, i)
            if ts_results:
                o,s=ts_results.group(0),ts_results.group(0).lower()
                i=i+len(s)
                if i < l and st[i]=='.': i=i+1
                # Check for month name:
                if MonthNumbers.has_key(s):
                    v=MonthNumbers[s]
                    if month is None: month=v
                    else: raise SyntaxError, st
                    continue
                # Check for time modifier:
                if s in TimeModifiers:
                    if tm is None: tm=s
                    else: raise SyntaxError, st
                    continue
                # Check for and skip day of week:
                if DayOfWeekNames.has_key(s):
                    continue

            raise SyntaxError, st

        day=None
        if ints[-1] > 60 and d not in ['.',':','/'] and len(ints) > 2:
            year=ints[-1]
            del ints[-1]
            if month:
                day=ints[0]
                del ints[:1]
            else:
                month=ints[0]
                day=ints[1]
                del ints[:2]
        elif month:
            if len(ints) > 1:
                if ints[0] > 31:
                    year=ints[0]
                    day=ints[1]
                else:
                    year=ints[1]
                    day=ints[0]
                del ints[:2]
        elif len(ints) > 2:
            if ints[0] > 31:
                year=ints[0]
                if ints[1] > 12:
                    day=ints[1]
                    month=ints[2]
                else:
                    day=ints[2]
                    month=ints[1]
            if ints[1] > 31:
                year=ints[1]
                if ints[0] > 12 and ints[2] <= 12:
                    day=ints[0]
                    month=ints[2]
                elif ints[2] > 12 and ints[0] <= 12:
                    day=ints[2]
                    month=ints[0]
            elif ints[2] > 31:
                year=ints[2]
                if ints[0] > 12:
                    day=ints[0]
                    month=ints[1]
                else:
                    if datefmt=="us":
                        day=ints[1]
                        month=ints[0]
                    else:
                        day=ints[0]
                        month=ints[1]

            elif ints[0] <= 12:
                month=ints[0]
                day=ints[1]
                year=ints[2]
            del ints[:3]

        if day is None:
            # Use today's date.
            year,month,day = localtime(time())[:3]

        year = _correctYear(year)
        if year < 1000: raise SyntaxError, st

        leap = year%4==0 and (year%100!=0 or year%400==0)
        try:
            if not day or day > self._month_len[leap][month]:
                raise DateError, st
        except IndexError:
            raise DateError, st
        tod=0
        if ints:
            i=ints[0]
            # Modify hour to reflect am/pm
            if tm and (tm=='pm') and i<12:  i=i+12
            if tm and (tm=='am') and i==12: i=0
            if i > 24: raise TimeError, st
            tod = tod + int(i) * 3600
            del ints[0]
            if ints:
                i=ints[0]
                if i > 60: raise TimeError, st
                tod = tod + int(i) * 60
                del ints[0]
                if ints:
                    i=ints[0]
                    if i > 60: raise TimeError, st
                    tod = tod + i
                    del ints[0]
                    if ints: raise SyntaxError,st


        tod_int = int(math.floor(tod))
        ms = tod - tod_int
        hr,mn,sc = _calcHMS(tod_int, ms)
        if not tz:
            # Figure out what time zone it is in the local area
            # on the given date.
            x = _calcDependentSecond2(year,month,day,hr,mn,sc)
            tz = self._calcTimezoneName(x, ms)

        return year,month,day,hr,mn,sc,tz

    # Internal methods
    def __getinitargs__(self): return (None,)


    def _validDate(self,y,m,d):
        if m<1 or m>12 or y<0 or d<1 or d>31: return 0
        return d<=self._month_len[(y%4==0 and (y%100!=0 or y%400==0))][m]

    def _validTime(self,h,m,s):
        return h>=0 and h<=23 and m>=0 and m<=59 and s>=0 and s < 60

    def __getattr__(self, name):
        if '%' in name: return strftimeFormatter(self, name)
        raise AttributeError, name


    # Conversion and comparison methods
    def timeTime(self):
        """Return the date/time as a floating-point number in UTC,
           in the format used by the python time module.
           Note that it is possible to create date/time values
           with DateTime that have no meaningful value to the
           time module."""
        return self._t

    def toZone(self, z):
        """Return a DateTime with the value as the current
           object, represented in the indicated timezone."""
        t,tz=self._t,self._tzinfo._zmap[z.lower()]
        millis = self.millis()
        #if (t>0 and ((t/86400.0) < 24837)):
        try:
            # Try to use time module for speed.
            yr,mo,dy,hr,mn,sc=safegmtime(t+_tzoffset(tz, t))[:6]
            sc=self._second
            return self.__class__(yr,mo,dy,hr,mn,sc,tz,t,
                                  self._d,self.time,millis)
        except:  # gmtime can't perform the calculation in the given range.
            # Calculate the difference between the two time zones.
            tzdiff = _tzoffset(tz, t) - _tzoffset(self._tz, t)
            if tzdiff == 0:
                return self
            sc = self._second
            ms = sc - math.floor(sc)
            x = _calcDependentSecond2(self._year, self._month, self._day,
                                      self._hour, self._minute, sc)
            x_new = x + tzdiff
            yr,mo,dy,hr,mn,sc = _calcYMDHMS(x_new, ms)
            return self.__class__(yr,mo,dy,hr,mn,sc,tz,t,
                                  self._d,self.time,millis)

    def isFuture(self):
        """Return true if this object represents a date/time
           later than the time of the call"""
        return (self._t > time())

    def isPast(self):
        """Return true if this object represents a date/time
           earlier than the time of the call"""
        return (self._t < time())

    def isCurrentYear(self):
        """Return true if this object represents a date/time
           that falls within the current year, in the context
           of this object\'s timezone representation"""
        t=time()
        return safegmtime(t+_tzoffset(self._tz, t))[0]==self._year

    def isCurrentMonth(self):
        """Return true if this object represents a date/time
           that falls within the current month, in the context
           of this object\'s timezone representation"""
        t=time()
        gmt=safegmtime(t+_tzoffset(self._tz, t))
        return gmt[0]==self._year and gmt[1]==self._month

    def isCurrentDay(self):
        """Return true if this object represents a date/time
           that falls within the current day, in the context
           of this object\'s timezone representation"""
        t=time()
        gmt=safegmtime(t+_tzoffset(self._tz, t))
        return gmt[0]==self._year and gmt[1]==self._month and gmt[2]==self._day

    def isCurrentHour(self):
        """Return true if this object represents a date/time
           that falls within the current hour, in the context
           of this object\'s timezone representation"""
        t=time()
        gmt=safegmtime(t+_tzoffset(self._tz, t))
        return (gmt[0]==self._year and gmt[1]==self._month and
                gmt[2]==self._day and gmt[3]==self._hour)

    def isCurrentMinute(self):
        """Return true if this object represents a date/time
           that falls within the current minute, in the context
           of this object\'s timezone representation"""
        t=time()
        gmt=safegmtime(t+_tzoffset(self._tz, t))
        return (gmt[0]==self._year and gmt[1]==self._month and
                gmt[2]==self._day and gmt[3]==self._hour and
                gmt[4]==self._minute)

    def earliestTime(self):
        """Return a new DateTime object that represents the earliest
           possible time (in whole seconds) that still falls within
           the current object\'s day, in the object\'s timezone context"""
        return self.__class__(self._year,self._month,self._day,0,0,0,self._tz)

    def latestTime(self):
        """Return a new DateTime object that represents the latest
           possible time (in whole seconds) that still falls within
           the current object\'s day, in the object\'s timezone context"""
        return self.__class__(self._year,self._month,self._day,
                              23,59,59,self._tz)

    def greaterThan(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned
           by the python time module. Returns true if the object
           represents a date/time greater than the specified DateTime
           or time module style time.
           Revised to give more correct results through comparison of
           long integer milliseconds.
           """
        # Optimized for sorting speed
        try:
            return (self._millis > t._millis)
        except AttributeError:
            try: self._millis
            except AttributeError: self._upgrade_old()
        return (self._t > t)

    __gt__ = greaterThan

    def greaterThanEqualTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned
           by the python time module. Returns true if the object
           represents a date/time greater than or equal to the
           specified DateTime or time module style time.
           Revised to give more correct results through comparison of
           long integer milliseconds.
           """
        # Optimized for sorting speed
        try:
            return (self._millis >= t._millis)
        except AttributeError:
            try: self._millis
            except AttributeError: self._upgrade_old()
        return (self._t >= t)

    __ge__ = greaterThanEqualTo

    def equalTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned
           by the python time module. Returns true if the object
           represents a date/time equal to the specified DateTime
           or time module style time.
           Revised to give more correct results through comparison of
           long integer milliseconds.
           """
        # Optimized for sorting speed
        try:
            return (self._millis == t._millis)
        except AttributeError:
            try: self._millis
            except AttributeError: self._upgrade_old()
        return (self._t == t)

    __eq__ = equalTo

    def notEqualTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned
           by the python time module. Returns true if the object
           represents a date/time not equal to the specified DateTime
           or time module style time.
           Revised to give more correct results through comparison of
           long integer milliseconds.
           """
        # Optimized for sorting speed
        try:
            return (self._millis != t._millis)
        except AttributeError:
            try: self._millis
            except AttributeError: self._upgrade_old()
        return (self._t != t)

    __ne__ = notEqualTo

    def lessThan(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned
           by the python time module. Returns true if the object
           represents a date/time less than the specified DateTime
           or time module style time.
           Revised to give more correct results through comparison of
           long integer milliseconds.
           """
        # Optimized for sorting speed
        try:
            return (self._millis < t._millis)
        except AttributeError:
            try: self._millis
            except AttributeError: self._upgrade_old()
        return (self._t < t)

    __lt__ = lessThan

    def lessThanEqualTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned
           by the python time module. Returns true if the object
           represents a date/time less than or equal to the specified
           DateTime or time module style time.
           Revised to give more correct results through comparison of
           long integer milliseconds.
           """
        # Optimized for sorting speed
        try:
            return (self._millis <= t._millis)
        except AttributeError:
            try: self._millis
            except AttributeError: self._upgrade_old()
        return (self._t <= t)

    __le__ = lessThanEqualTo

    def isLeapYear(self):
        """Return true if the current year (in the context of the object\'s
           timezone) is a leap year"""
        return self._year%4==0 and (self._year%100!=0 or self._year%400==0)

    def dayOfYear(self):
        """Return the day of the year, in context of
           the timezone representation of the object"""
        d=int(self._d+(_tzoffset(self._tz, self._t)/86400.0))
        return int((d+jd1901)-_julianday(self._year,1,0))


    # Component access
    def parts(self):
        """Return a tuple containing the calendar year, month,
           day, hour, minute second and timezone of the object"""
        return self._year, self._month, self._day, self._hour, \
               self._minute, self._second, self._tz

    def timezone(self):
        """Return the timezone in which the object is represented."""
        return self._tz

    def tzoffset(self):
        """Return the timezone offset for the objects timezone."""
        return _tzoffset(self._tz, self._t)

    def year(self):
        """Return the calendar year of the object"""
        return self._year

    def month(self):
        """Return the month of the object as an integer"""
        return self._month

    def Month(self):
        """Return the full month name"""
        return self._fmon

    def aMonth(self):
        """Return the abreviated month name."""
        return self._amon

    def Mon(self):
        """Compatibility: see aMonth"""
        return self._amon

    def pMonth(self):
        """Return the abreviated (with period) month name."""
        return self._pmon

    def Mon_(self):
        """Compatibility: see pMonth"""
        return self._pmon

    def day(self):
        """Return the integer day"""
        return self._day

    def Day(self):
        """Return the full name of the day of the week"""
        return self._fday

    def DayOfWeek(self):
        """Compatibility: see Day"""
        return self._fday

    def aDay(self):
        """Return the abreviated name of the day of the week"""
        return self._aday

    def pDay(self):
        """Return the abreviated (with period) name of the day of the week"""
        return self._pday

    def Day_(self):
        """Compatibility: see pDay"""
        return self._pday

    def dow(self):
        """Return the integer day of the week, where sunday is 0"""
        return self._dayoffset

    def dow_1(self):
        """Return the integer day of the week, where sunday is 1"""
        return self._dayoffset+1

    def h_12(self):
        """Return the 12-hour clock representation of the hour"""
        return self._pmhour

    def h_24(self):
        """Return the 24-hour clock representation of the hour"""
        return self._hour

    def ampm(self):
        """Return the appropriate time modifier (am or pm)"""
        return self._pm

    def hour(self):
        """Return the 24-hour clock representation of the hour"""
        return self._hour

    def minute(self):
        """Return the minute"""
        return self._minute

    def second(self):
        """Return the second"""
        return self._second

    def millis(self):
        """Return the millisecond since the epoch in GMT."""
        try:
            return self._millis
        except AttributeError:
            return self._upgrade_old()

    def _upgrade_old(self):
        """Upgrades a previously pickled DateTime object."""
        millis = long(math.floor(self._t * 1000.0))
        self._millis = millis
        return millis

    def strftime(self, format):
        # Format the date/time using the *current timezone representation*.
        x      = _calcDependentSecond2(self._year, self._month, self._day, 
                 self._hour, self._minute, self._second)
        ltz    = self._calcTimezoneName(x, 0)
        tzdiff = _tzoffset(ltz, self._t) - _tzoffset(self._tz, self._t)
        zself  = self + tzdiff/86400.0
        microseconds = int((zself._second - zself._nearsec) * 1000000)

        # Note: in older versions strftime() accepted also unicode strings
        # as format strings (just because time.strftime() did not perform
        # any type checking). So we convert unicode strings to utf8,
        # pass them to strftime and convert them back to unicode if necessary.

        format_is_unicode = False
        if isinstance(format, unicode):
            format = format.encode('utf-8')
            format_is_unicode = True
        ds = datetime(zself._year, zself._month, zself._day, zself._hour,  
               zself._minute, int(zself._nearsec), 
               microseconds).strftime(format) 
        return format_is_unicode and unicode(ds, 'utf-8') or ds


    # General formats from previous DateTime
    def Date(self):
        """Return the date string for the object."""
        return "%s/%2.2d/%2.2d" % (self._year, self._month, self._day)

    def Time(self):
        """Return the time string for an object to the nearest second."""
        return '%2.2d:%2.2d:%2.2d' % (self._hour,self._minute,self._nearsec)

    def TimeMinutes(self):
        """Return the time string for an object not showing seconds."""
        return '%2.2d:%2.2d' % (self._hour,self._minute)

    def AMPM(self):
        """Return the time string for an object to the nearest second."""
        return '%2.2d:%2.2d:%2.2d %s' % (
                self._pmhour,self._minute,self._nearsec,self._pm)

    def AMPMMinutes(self):
        """Return the time string for an object not showing seconds."""
        return '%2.2d:%2.2d %s' % (self._pmhour,self._minute,self._pm)

    def PreciseTime(self):
        """Return the time string for the object."""
        return '%2.2d:%2.2d:%06.3f' % (self._hour,self._minute,self._second)

    def PreciseAMPM(self):
        """Return the time string for the object."""
        return '%2.2d:%2.2d:%06.3f %s' % (
                self._pmhour,self._minute,self._second,self._pm)

    def yy(self):
        """Return calendar year as a 2 digit string"""
        return str(self._year)[-2:]

    def mm(self):
        """Return month as a 2 digit string"""
        return '%02d' % self._month

    def dd(self):
        """Return day as a 2 digit string"""
        return '%02d' % self._day

    def rfc822(self):
        """Return the date in RFC 822 format"""
        tzoffset = _tzoffset2rfc822zone(_tzoffset(self._tz, self._t))

        return '%s, %2.2d %s %d %2.2d:%2.2d:%2.2d %s' % (
            self._aday,self._day,self._amon,self._year,
            self._hour,self._minute,self._nearsec,tzoffset)

    # New formats
    def fCommon(self):
        """Return a string representing the object\'s value
           in the format: March 1, 1997 1:45 pm"""
        return '%s %s, %4.4d %s:%2.2d %s' % (
               self._fmon,self._day,self._year,self._pmhour,
               self._minute,self._pm)

    def fCommonZ(self):
        """Return a string representing the object\'s value
           in the format: March 1, 1997 1:45 pm US/Eastern"""
        return '%s %s, %4.4d %d:%2.2d %s %s' % (
               self._fmon,self._day,self._year,self._pmhour,
               self._minute,self._pm,self._tz)

    def aCommon(self):
        """Return a string representing the object\'s value
           in the format: Mar 1, 1997 1:45 pm"""
        return '%s %s, %4.4d %s:%2.2d %s' % (
               self._amon,self._day,self._year,self._pmhour,
               self._minute,self._pm)

    def aCommonZ(self):
        """Return a string representing the object\'s value
           in the format: Mar 1, 1997 1:45 pm US/Eastern"""
        return '%s %s, %4.4d %d:%2.2d %s %s' % (
               self._amon,self._day,self._year,self._pmhour,
               self._minute,self._pm,self._tz)

    def pCommon(self):
        """Return a string representing the object\'s value
           in the format: Mar. 1, 1997 1:45 pm"""
        return '%s %s, %4.4d %s:%2.2d %s' % (
               self._pmon,self._day,self._year,self._pmhour,
               self._minute,self._pm)

    def pCommonZ(self):
        """Return a string representing the object\'s value
           in the format: Mar. 1, 1997 1:45 pm US/Eastern"""
        return '%s %s, %4.4d %d:%2.2d %s %s' % (
               self._pmon,self._day,self._year,self._pmhour,
               self._minute,self._pm,self._tz)


    def ISO(self):
        """Return the object in ISO standard format. Note:
        this is *not* ISO 8601-format! See the ISO8601 and
        HTML4 methods below for ISO 8601-compliant output

        Dates are output as: YYYY-MM-DD HH:MM:SS
        """
        return "%.4d-%.2d-%.2d %.2d:%.2d:%.2d" % (
            self._year, self._month, self._day,
            self._hour, self._minute, self._second)

    def ISO8601(self):
        """Return the object in ISO 8601-compatible format containing
        the date, time with seconds-precision and the time zone
        identifier - see http://www.w3.org/TR/NOTE-datetime

        Dates are output as: YYYY-MM-DDTHH:MM:SSTZD
            T is a literal character.
            TZD is Time Zone Designator, format +HH:MM or -HH:MM

        The HTML4 method below offers the same formatting, but converts
        to UTC before returning the value and sets the TZD "Z"
        """
        tzoffset = _tzoffset2iso8601zone(_tzoffset(self._tz, self._t))

        return  "%0.4d-%0.2d-%0.2dT%0.2d:%0.2d:%0.2d%s" % (
            self._year, self._month, self._day,
            self._hour, self._minute, self._second, tzoffset)

    def HTML4(self):
        """Return the object in the format used in the HTML4.0 specification,
        one of the standard forms in ISO8601.  See
               http://www.w3.org/TR/NOTE-datetime

        Dates are output as: YYYY-MM-DDTHH:MM:SSZ
           T, Z are literal characters.
           The time is in UTC.
        """

        newdate = self.toZone('UTC')
        return "%0.4d-%0.2d-%0.2dT%0.2d:%0.2d:%0.2dZ" % (
            newdate._year, newdate._month, newdate._day,
            newdate._hour, newdate._minute, newdate._second)

    def __add__(self,other):
        """A DateTime may be added to a number and a number may be
           added to a DateTime;  two DateTimes cannot be added."""
        if hasattr(other,'_t'):
            raise DateTimeError,'Cannot add two DateTimes'
        o=float(other)
        tz = self._tz
        t = (self._t + (o*86400.0))
        d = (self._d + o)
        s = d - math.floor(d)
        ms = t - math.floor(t)
        x = _calcDependentSecond(tz, t)
        yr,mo,dy,hr,mn,sc = _calcYMDHMS(x, ms)
        return self.__class__(yr,mo,dy,hr,mn,sc,self._tz,t,d,s)
    __radd__=__add__

    def __sub__(self,other):
        """Either a DateTime or a number may be subtracted from a
           DateTime, however, a DateTime may not be subtracted from
           a number."""
        if hasattr(other, '_d'):
            if 0:  # This logic seems right but is incorrect.
                my_t = self._t + _tzoffset(self._tz, self._t)
                ob_t = other._t + _tzoffset(other._tz, other._t)
                return (my_t - ob_t) / 86400.0
            return self._d - other._d
        else:
            return self.__add__(-(other))

    def __repr__(self):
        """Convert a DateTime to a string that
           looks like a Python expression."""
        return '%s(\'%s\')' % (self.__class__.__name__,str(self))

    def __str__(self):
        """Convert a DateTime to a string."""
        y,m,d   =self._year,self._month,self._day
        h,mn,s,t=self._hour,self._minute,self._second,self._tz
        if h == mn == s == 0:
            # hh:mm:ss all zero -- suppress the time.
            return '%4.4d/%2.2d/%2.2d' % (y, m, d)
        elif s == int(s):
            # A whole number of seconds -- suppress milliseconds.
            return '%4.4d/%2.2d/%2.2d %2.2d:%2.2d:%2.2d %s' % (
                    y, m, d, h, mn, s, t)
        else:
            # s is already rounded to the nearest millisecond, and
            # it's not a whole number of seconds.  Be sure to print
            # 2 digits before the decimal point.
            return '%4.4d/%2.2d/%2.2d %2.2d:%2.2d:%06.3f %s' % (
                    y, m, d, h, mn, s, t)

    def __cmp__(self,obj):
        """Compare a DateTime with another DateTime object, or
           a float such as those returned by time.time().

           NOTE: __cmp__ support is provided for backward
           compatibility only, and mixing DateTimes with
           ExtensionClasses could cause __cmp__ to break.
           You should use the methods lessThan, greaterThan,
           lessThanEqualTo, greaterThanEqualTo, equalTo and
           notEqualTo to avoid potential problems later!!"""
        # Optimized for sorting speed.
        try:
            return cmp(self._millis, obj._millis)
        except AttributeError:
            try: self._millis
            except AttributeError: self._upgrade_old()
        return cmp(self._t,obj)

    def __hash__(self):
        """Compute a hash value for a DateTime"""
        return int(((self._year%100*12+self._month)*31+
                     self._day+self.time)*100)

    def __int__(self):
        """Convert to an integer number of seconds since the epoch (gmt)"""
        return int(self.millis() / 1000)

    def __long__(self):
        """Convert to a long-int number of seconds since the epoch (gmt)"""
        return long(self.millis() / 1000)

    def __float__(self):
        """Convert to floating-point number of seconds since the epoch (gmt)"""
        return float(self._t)

    def _parse_iso8601(self,s):
        try:
            return self.__parse_iso8601(s)
        except IndexError:
            raise SyntaxError, (
                'Not an ISO 8601 compliant date string: "%s"' % s)

    def __parse_iso8601(self,s):
        """ parse an ISO 8601 compliant date """
        year=0
        month=day=1
        hour=minute=seconds=hour_off=min_off=0

        datereg = re.compile('([0-9]{4})(-([0-9][0-9]))?(-([0-9][0-9]))?')
        timereg = re.compile('T([0-9]{2})(:([0-9][0-9]))?(:([0-9][0-9]))?(\.[0-9]{1,20})?')
        zonereg = re.compile('([+-][0-9][0-9])(:?([0-9][0-9]))')

        # Date part

        fields = datereg.split(s.strip(), 1)

        if fields[1]:   year  = int(fields[1])
        if fields[3]:   month = int(fields[3])
        if fields[5]:   day   = int(fields[5])
        t = fields[6]
        if t:
            if not fields[5]:
                # Specifying time requires specifying a day.
                raise IndexError

            fields = timereg.split(t)

            if fields[1]:   hour     = int(fields[1])
            if fields[3]:   minute   = int(fields[3])
            if fields[5]:   seconds  = int(fields[5])
            if fields[6]:   seconds  = seconds+float(fields[6])
            z = fields[7]

            if z and z.startswith('Z'):
                # Waaaa! This is wrong, since 'Z' and '+HH:MM'
                # are supposed to be mutually exclusive.
                # It's only here to prevent breaking 2.7 beta.
                z = z[1:]

            if z:
                fields = zonereg.split(z)
                hour_off = int(fields[1])
                min_off  = int(fields[3])
                if fields[4]:
                    # Garbage after time zone
                    raise IndexError

        return year,month,day,hour,minute,seconds,'GMT%+03d%02d' % (hour_off,min_off)

    def JulianDay(self):
        """
        Return the Julian day according to
        http://www.tondering.dk/claus/cal/node3.html#sec-calcjd
        """
        a = (14 - self._month)/12 #integer division, discard remainder
        y = self._year + 4800 - a
        m = self._month + (12*a) - 3
        return self._day + (153*m+2)/5 + 365*y + y/4 - y/100 + y/400 - 32045

    def week(self):
        """
        Return the week number according to ISO
        see http://www.tondering.dk/claus/cal/node6.html#SECTION00670000000000000000
        """
        J = self.JulianDay()
        d4 = (J + 31741 - (J % 7)) % 146097 % 36524 % 1461
        L = d4/1460
        d1 = (( d4 - L) % 365) + L
        return d1/7 + 1

    def encode(self, out):
        """
        Encode value for XML-RPC
        """
        out.write('<value><dateTime.iso8601>')
        out.write(self.ISO8601())
        out.write('</dateTime.iso8601></value>\n')


class strftimeFormatter:

    def __init__(self, dt, format):
        self._dt=dt
        self._f=format

    def __call__(self): return self._dt.strftime(self._f)


# Module methods
def Timezones():
    """Return the list of recognized timezone names"""
    return _cache._zlst

