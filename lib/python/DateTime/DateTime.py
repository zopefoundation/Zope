##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Encapsulation of date/time values"""

__version__='$Revision: 1.29 $'[11:-2]


import sys,os,regex,DateTimeZone
from string import strip,split,upper,lower,atoi,atof,find,join
from time import time,gmtime,localtime,asctime,tzname,strftime,mktime
from types import InstanceType,IntType,FloatType,StringType







# Determine machine epoch
tm=((0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334),
    (0, 0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335))
yr,mo,dy,hr,mn,sc=gmtime(0)[:6]
i=int(yr-1)
to_year =int(i*365+i/4-i/100+i/400-693960.0)
to_month=tm[yr%4==0 and (yr%100!=0 or yr%400==0)][mo]
EPOCH  =(to_year+to_month+dy+(hr/24.0+mn/1440.0+sc/86400.0))*86400
CENTURY=1900
jd1901 =2415385L


numericTimeZoneMatch=regex.compile('[+-][\0-\9][\0-\9][\0-\9][\0-\9]').match



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
        return self.tinfo[idx][0],self.tinfo[idx][1],zs[:find(zs,'\000')]




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
           'UT','BST','CDT','MEST','SST','FST','WADT','EADT','NZDT',
           'WET','WAT','AT','AST','NT','IDLW','CET','MET',
           'MEWT','SWT','FWT','EET','BT','ZP4','ZP5','ZP6',
           'WAST','CCT','JST','EAST','GST','NZT','NZST','IDLE']


    _zmap={'aest':'GMT+1000', 'aedt':'GMT+1100',
           'aus eastern standard time':'GMT+1000',
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
           'cst':'Us/Central','cuba':'Cuba','est':'US/Eastern','egypt':'Egypt',
           'eastern standard time':'US/Eastern',
           'us eastern standard time':'US/Eastern',
           'central standard time':'US/Central',
           'mountain standard time':'US/Mountain',
           'pacific standard time':'US/Pacific',
           'gb-eire':'GB-Eire','gmt':'GMT',

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
           'bst':'GMT+1', 'cdt':'GMT+2', 'mest':'GMT+2', 'sst':'GMT+2',
           'fst':'GMT+2', 'wadt':'GMT+8', 'eadt':'GMT+11', 'nzdt':'GMT+13',
           'wet':'GMT', 'wat':'GMT-1', 'at':'GMT-2', 'ast':'GMT-4',
           'nt':'GMT-11', 'idlw':'GMT-12', 'cet':'GMT+1', 'met':'GMT+1',
           'mewt':'GMT+1', 'swt':'GMT+1', 'fwt':'GMT+1', 'eet':'GMT+2',
           'bt':'GMT+3', 'zp4':'GMT+4', 'zp5':'GMT+5', 'zp6':'GMT+6',
           'wast':'GMT+7', 'cct':'GMT+8', 'jst':'GMT+9', 'east':'GMT+10',
           'gst':'GMT+10', 'nzt':'GMT+12', 'nzst':'GMT+12', 'idle':'GMT+12'
           }


    def __init__(self):
        self._db=DateTimeZone._data
        self._d,self._zidx={},self._zmap.keys()

    def __getitem__(self,k):
        try:   n=self._zmap[lower(k)]
        except KeyError:
            if numericTimeZoneMatch(k) <= 0:
                raise 'DateTimeError','Unrecognized timezone: %s' % k
            return k
        try: return self._d[n]
        except KeyError:
            z=self._d[n]=_timezone(self._db[n])
            return z







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

    def __init__(self,*args):
        """Return a new date-time object

        A DateTime object always maintains its value as an absolute 
        UTC time, and is represented in the context of some timezone
        based on the arguments used to create the object. A DateTime
        object's methods return values based on the timezone context.

        Note that in all cases the local machine timezone is used for
        representation if no timezone is specified.

        DateTimes may be created with from zero to seven arguments.


          - If the function is called with no arguments, then the 
            current date/time is returned, represented in the 
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
            DateTimeError is raised. Two-digit years are assumed
            to be in the twentieth century. The fourth, fifth, and
            sixth arguments are floating point, positive or
            negative offsets in units of hours, minutes, and days,
            and default to zero if not given. An optional string may
            be given as the final argument to indicate timezone (the
            effect of this is as if you had taken the value of time.time()
            at that time on a machine in the specified timezone).

        If a string argument passed to the DateTime constructor cannot be
        parsed, it will raise DateTime.SyntaxError. Invalid date, time, or
        timezone components will raise a DateTime.DateTimeError. 

        The module function Timezones() will return a list of the 
        timezones recognized by the DateTime module. Recognition of 
        timezone names is case-insensitive.""" #'

        d=t=s=None
        ac=len(args)

        if ac and args[0]==None: return
        elif ac==10:
            # Internal format called only by DateTime
            yr,mo,dy,hr,mn,sc,tz,t,d,s=args

        elif not args:
            # Current time, exp in local timezone
            t,tz=time(),self._localzone
            ms=(t-int(t))
            yr,mo,dy,hr,mn,sc=gmtime(int(t))[:6]
            s=(hr/24.0+mn/1440.0+(sc+ms)/86400.0)
            d=(self._julianday(yr,mo,dy)-jd1901)+s
            yr,mo,dy,hr,mn,sc=localtime(t)[:6]
            sc=sc+ms
            
        elif ac==1:
            arg=args[0]
            
            if arg=='':
                raise self.SyntaxError, arg
            
            if type(arg)==StringType and lower(arg) in self._tzinfo._zidx:
                # Current time, exp in specified timezone
                t,tz=time(),self._tzinfo._zmap[lower(arg)]
                ms=(t-int(t))
                yr,mo,dy,hr,mn,sc=gmtime(t)[:6]
                s=(hr/24.0+mn/1440.0+(sc+ms)/86400.0)
                d=(self._julianday(yr,mo,dy)-jd1901)+s
                x=d+(self._tzinfo[tz].info(t)[0]/86400.0)
                yr,mo,dy=self._calendarday(x+jd1901)
                x=(x-int(x))*86400.0
                hr=int(x/3600)
                x=x-(hr*3600)
                mn=int(x/60)
                sc=x-(mn*60)

            elif type(arg)==StringType:
                # Date/time string
                yr,mo,dy,hr,mn,sc,tz=self._parse(arg)
                
                try: tz=self._tzinfo._zmap[lower(tz)]
                except KeyError:
                    if numericTimeZoneMatch(tz) <= 0:
                        raise self.DateTimeError, 'Invalid date: %s' % arg
                if not self._validDate(yr,mo,dy):
                    raise self.DateTimeError, 'Invalid date: %s' % arg
                if not self._validTime(hr,mn,int(sc)):
                    raise self.DateTimeError, 'Invalid time: %s' % arg
                s=(hr/24.0+mn/1440.0+sc/86400.0)
                d=(self._julianday(yr,mo,dy)-jd1901)+s
                t=(d*86400.0)-EPOCH+86400.0
                try:
                    a=self._tzinfo[tz].info(t)[0]
                except:
                    if numericTimeZoneMatch(tz) > 0:
                        a=atoi(tz[1:3])*3600+atoi(tz[3:5])*60
                        
                d,t=d-(a/86400.0),t-a
                        

            else:
                # Seconds from epoch, gmt
                t,tz=arg,self._localzone
                ms=(t-int(t))
                yr,mo,dy,hr,mn,sc=gmtime(int(t))[:6]
                s=(hr/24.0+mn/1440.0+(sc+ms)/86400.0)
                d=(self._julianday(yr,mo,dy)-jd1901)+s
                yr,mo,dy,hr,mn,sc=localtime(t)[:6]
                sc=sc+ms

        elif ac==2:
            if type(args[1])==StringType:
                # Seconds from epoch (gmt) and timezone
                t,tz=args
                ms=(t-int(t))
                tz=self._tzinfo._zmap[lower(tz)]
                yr,mo,dy,hr,mn,sc=gmtime(t)[:6]
                s=(hr/24.0+mn/1440.0+(sc+ms)/86400.0)
                d=(self._julianday(yr,mo,dy)-jd1901)+s
                x=d+(self._tzinfo[tz].info(t)[0]/86400.0)
                yr,mo,dy=self._calendarday(x+jd1901)
                x=(x-int(x))*86400.0
                hr=int(x/3600)
                x=x-(hr*3600)
                mn=int(x/60)
                sc=x-(mn*60)
                if(hr==23 and mn==59 and sc>59.999):
                    # Fix formatting for positives
                    hr,mn,sc=0,0,0.0
                else:
                    # Fix formatting for negatives
                    if hr<0: hr=23+hr
                    if mn<0: mn=59+mn
                    if sc<0:
                        if (sc-int(sc)>=0.999): sc=round(sc)
                        sc=59+sc
            else:
                # Year, julean expressed in local zone
                tz=self._localzone
                yr,jul=args
                if not yr>100: yr=yr+CENTURY
                d=(self._julianday(yr,1,0)-jd1901)+jul
                yr,mo,dy=self._calendarday(d+jd1901)
                x=(d-int(d))*86400.0
                hr=int(x/3600)
                x=x-(hr*3600)
                mn=int(x/60)
                sc=x-(mn*60)
                if(hr==23 and mn==59 and sc>59.999):
                    # Fix formatting for positives
                    hr,mn,sc=0,0,0.0
                else:
                    # Fix formatting for negatives
                    if hr<0: hr=23+hr
                    if mn<0: mn=59+mn
                    if sc<0:
                        if (sc-int(sc)>=0.999): sc=round(sc)
                        sc=59+sc
                d=d-(self._tzinfo[tz].info(t)[0]/86400.0)
                s=d-int(d)
                t=(d*86400.0)-EPOCH
        else:
            # Explicit format
            yr,mo,dy=args[:3]
            hr,mn,sc,tz=0,0,0,0
            yr=(yr>100) and yr or yr+CENTURY
            if not self._validDate(yr,mo,dy):
                raise self.DateTimeError, 'Invalid date: %s' % args
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
                                raise self.DateTimeError,'Too many arguments'
            if not self._validTime(hr,mn,sc):
                raise self.DateTimeError, 'Invalid time: %s' % `args`
            if not tz: tz=self._localzone
            else:      tz=self._tzinfo._zmap[lower(tz)]
            leap=yr%4==0 and (yr%100!=0 or yr%400==0)
            s=(hr/24.0+mn/1440.0+sc/86400.0)
            d=(self._julianday(yr,mo,dy)-jd1901)+s
            t=(d*86400.0)-EPOCH+86400.0
            a=self._tzinfo[tz].info(t)[0]
            d,t=d-(a/86400.0),t-a

        if hr>12:
            self._pmhour=hr-12
            self._pm='pm'
        else:
            self._pmhour=hr or 12
            self._pm= (hr==12) and 'pm' or 'am'
        self._dayoffset=dx=int((self._julianday(yr,mo,dy)+2L)%7)
        self._fmon,self._amon,self._pmon= \
            self._months[mo],self._months_a[mo],self._months_p[mo]
        self._fday,self._aday,self._pday= \
            self._days[dx],self._days_a[dx],self._days_p[dx]
        self._nearsec=round(sc)
        self._year,self._month,self._day     =yr,mo,dy
        self._hour,self._minute,self._second =hr,mn,sc
        self.time,self._d,self._t,self._tz   =s,d,t,tz


    DateTimeError='DateTimeError'
    SyntaxError  ='Invalid Date-Time String'
    DateError    ='Invalid Date Components'
    int_pattern  =regex.compile('\([0-9]+\)')
    flt_pattern  =regex.compile('\([0-9]+\.[0-9]+\)')
    name_pattern =regex.compile('\([a-z][a-z]+\)', regex.casefold)
    space_chars  =' \t\n'
    delimiters   ='-/.:,'
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
    try: _localzone  =_cache._zmap[lower(tzname[0])]
    except: _localzone=''
    _tzinfo     =_cache()

    def _parse(self,string):
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
        sp=split(strip(string))
        tz=sp[-1]
        if tz and (lower(tz) in ValidZones): string=join(sp[:-1])
        else: tz=self._localzone

        ints,dels=[],[]
        i,l=0,len(string)
        while i < l:
            while i < l and string[i] in spaces    : i=i+1
            if i < l and string[i] in delimiters:
                d=string[i]
                i=i+1
            else: d=''
            while i < l and string[i] in spaces    : i=i+1

            if fltpat.match(string,i) >= 0:
                s=fltpat.group(1)
                i=i+len(s)
                ints.append(atof(s))
                continue

            if intpat.match(string,i) >= 0:
                s=intpat.group(1)
                ls=len(s)
                i=i+ls
                if (ls==4 and d and d in '+-' and
                    (len(ints) + (not not month) >= 3)):
                    tz='%s%s' % (d,s)
                else:
                    v=atoi(s)
                    ints.append(v)
                continue

            if wordpat.match(string,i) >= 0:
                o,s=wordpat.group(1),lower(wordpat.group(1))
                i=i+len(s)
                if i < l and string[i]=='.': i=i+1
                # Check for month name:
                if MonthNumbers.has_key(s):
                    v=MonthNumbers[s]
                    if month is None: month=v
                    else: raise self.SyntaxError, string
                    continue
                # Check for time modifier:
                if s in TimeModifiers:
                    if tm is None: tm=s
                    else: raise self.SyntaxError, string
                    continue
                # Check for and skip day of week:
                if DayOfWeekNames.has_key(s):
                    continue
            raise self.SyntaxError, string

        day=None
        if ints[-1] > 60 and d not in ['.',':'] and len(ints) > 2:
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
                    day=ints[1]
                    month=ints[0]
            elif ints[0] <= 12:
                month=ints[0]
                day=ints[1]
                year=ints[2]
            del ints[:3]
            
        if day is None: raise self.SyntaxError, string

        if year < 100: year=year+CENTURY
        elif year < 1000: raise self.SyntaxError, string
        
        leap = year%4==0 and (year%100!=0 or year%400==0)
        if not day or day > self._month_len[leap][month]:
            raise self.SyntaxError, string
        t=0
        if ints:
            i=ints[0]
            # Modify hour to reflect am/pm
            if tm and (tm=='pm') and i<12:  i=i+12
            if tm and (tm=='am') and i==12: i=0
            if i > 24: raise self.SyntaxError, string
            t=t+i/24.0
            del ints[0]
            if ints:
                i=ints[0]
                if i > 60: raise self.SyntaxError, string
                t=t+i/1440.0
                del ints[0]
                if ints:
                    i=ints[0]
                    if i > 60: raise self.SyntaxError, string
                    t=t+i/86400.0
                    del ints[0]
                    if ints: raise self.SyntaxError,string

        t=t*86400.0
        hr=int(t/3600)
        t=t-hr*3600
        mn=int(t/60)
        sc=t-mn*60
        tz=tz or self._localzone
        return year,month,day,hr,mn,sc,tz



    # Internal methods
    def __getinitargs__(self): return (None,)

    def _julianday(self,yr,mo,dy):
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

    def _calendarday(self,j):
        j=long(j)
        if(j < 2299160L): b=j+1525L
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

    def _validDate(self,y,m,d):
        if m<1 or m>12 or y<0 or d<1 or d>31: return 0
        return d<=self._month_len[(y%4==0 and (y%100!=0 or y%400==0))][m]

    def _validTime(self,h,m,s):
        return h>=0 and h<=23 and m>=0 and m<=59 and s>=0 and s<=59

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
        t,tz=self._t,self._tzinfo._zmap[lower(z)]
        if (t>0 and ((t/86400.0) < 24837)):
            # Try to cheat and use time module for speed...
            yr,mo,dy,hr,mn,sc=gmtime(t+self._tzinfo[tz].info(t)[0])[:6]
            sc=self._second
            return self.__class__(yr,mo,dy,hr,mn,sc,tz,t,self._d,self.time)
        d=self._d+(self._tzinfo[tz].info(t)[0]/86400.0)
        yr,mo,dy=self._calendarday((d+jd1901))
        s=(d-int(d))*86400.0
        hr=int(s/3600)
        s=s-(hr*3600)
        mn=int(s/60)
        sc=s-(mn*60)
        if(hr==23 and mn==59 and sc>59.999):
            # Fix formatting for positives
            hr,mn,sc=0,0,0.0
        else:
            # Fix formatting for negatives
            if hr<0: hr=23+hr
            if mn<0: mn=59+mn
            if sc<0:
                if (sc-int(sc)>=0.999):
                    sc=round(sc)
                sc=59+sc
        return self.__class__(yr,mo,dy,hr,mn,sc,tz,t,self._d,self.time)

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
        return gmtime(t+self._tzinfo[self._tz].info(t)[0])[0]==self._year

    def isCurrentMonth(self):
        """Return true if this object represents a date/time
           that falls within the current month, in the context
           of this object\'s timezone representation"""
        t=time()
        return gmtime(t+self._tzinfo[self._tz].info(t)[0])[1]==self._month

    def isCurrentDay(self):
        """Return true if this object represents a date/time
           that falls within the current day, in the context
           of this object\'s timezone representation"""
        t=time()
        return gmtime(t+self._tzinfo[self._tz].info(t)[0])[2]==self._day

    def isCurrentHour(self):
        """Return true if this object represents a date/time
           that falls within the current hour, in the context
           of this object\'s timezone representation"""
        t=time()
        return gmtime(t+self._tzinfo[self._tz].info(t)[0])[3]==self._hour

    def isCurrentMinute(self):
        """Return true if this object represents a date/time
           that falls within the current minute, in the context
           of this object\'s timezone representation"""
        t=time()
        return gmtime(t+self._tzinfo[self._tz].info(t)[0])[4]==self._minute

    def earliestTime(self):
        """Return a new DateTime object that represents the earliest
           possible time (in whole seconds) that still falls within
           the current object\'s day, in the object\'s timezone context"""
        return self.__class__(self._year,self._month,self._day,0,0,1,self._tz)

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
           or time module style time."""
        try:    return (self._d > t._d)
        except: return (self._t > t)

    def greaterThanEqualTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned 
           by the python time module. Returns true if the object 
           represents a date/time greater than or equal to the 
           specified DateTime or time module style time."""
        try:    return (self._d >= t._d)
        except: return (self._t >= t)

    def equalTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned 
           by the python time module. Returns true if the object 
           represents a date/time equal to the specified DateTime
           or time module style time."""
        try:    return (self._d == t._d)
        except: return (self._t == t)

    def notEqualTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned 
           by the python time module. Returns true if the object 
           represents a date/time not equal to the specified DateTime
           or time module style time."""
        try:    return (self._d != t._d)
        except: return (self._t != t)

    def lessThan(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned 
           by the python time module. Returns true if the object 
           represents a date/time less than the specified DateTime
           or time module style time."""
        try:    return (self._d < t._d)
        except: return (self._t < t)

    def lessThanEqualTo(self,t):
        """Compare this DateTime object to another DateTime object
           OR a floating point number such as that which is returned 
           by the python time module. Returns true if the object 
           represents a date/time less than or equal to the specified 
           DateTime or time module style time."""
        try:    return (self._d <= t._d)
        except: return (self._t <= t)

    def isLeapYear(self):
        """Return true if the current year (in the context of the object\'s
           timezone) is a leap year"""
        return self._year%4==0 and (self._year%100!=0 or self._year%400==0)

    def dayOfYear(self):
        """Return the day of the year, in context of
           the timezone representation of the object"""
        d=int(self._d+(self._tzinfo[self._tz].info(self._t)[0]/86400.0))
        return int((d+jd1901)-self._julianday(self._year,1,0))


    # Component access
    def parts(self):
        """Return a tuple containing the calendar year, month,
           day, hour, minute second and timezone of the object"""
        return self._year, self._month, self._day, self._hour, \
               self._minute, self._second, self._tz

    def timezone(self):
        """Return the timezone in which the object is represented."""
        return self._tz

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

    def strftime(self, format):
        return strftime(format, gmtime(self.timeTime()))


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
        return '%s, %2.2d %s %d %2.2d:%2.2d:%2.2d %s' % (
            self._aday,self._day,self._amon,self._year,
            self._hour,self._minute,self._nearsec,self._tz)


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
        """Return the object in ISO standard format

        Dates are output as: YYYY-MM-DD HH:MM:SS
        """
        return "%.4d-%.2d-%.2d %.2d:%.2d:%.2d" % (
            self._year, self._month, self._day,
            self._hour, self._minute, self._second)

    def __add__(self,other):
        """A DateTime may be added to a number and a number may be 
           added to a DateTime;  two DateTimes cannot be added."""
        if hasattr(other,'_t'):
            raise self.DateTimeError,'Cannot add two DateTimes'
        o=float(other)
        d,t,tz=(self._d+o),(self._t+(o*86400.0)),self._tz
        x=d+(self._tzinfo[tz].info(t)[0]/86400.0)
        yr,mo,dy=self._calendarday((x+jd1901))
        s=(x-int(x))*86400.0
        hr=int(s/3600)
        s=s-(hr*3600)
        mn=int(s/60)
        s=s-(mn*60)
        return self.__class__(yr,mo,dy,hr,mn,s,self._tz,t,d,(d-int(d)))
    __radd__=__add__

    def __sub__(self,other):
        """Either a DateTime or a number may be subtracted from a
           DateTime, however, a DateTime may not be subtracted from 
           a number."""
        try:    return self._d-other._d
        except: return self.__add__(-(other))

    def __repr__(self):
        """Convert a DateTime to a string that 
           looks like a Python expression."""
        return '%s(\'%s\')' % (self.__class__.__name__,str(self))

    def __str__(self):
        """Convert a DateTime to a string."""
        y,m,d   =self._year,self._month,self._day
        h,mn,s,t=self._hour,self._minute,self._second,self._tz
        if(h+mn+s):
            if (s-int(s))> 0.0001:
                return '%4.4d/%2.2d/%2.2d %2.2d:%2.2d:%g %s' % (
                        y,m,d,h,mn,s,t)
            else:
                return '%4.4d/%2.2d/%2.2d  %2.2d:%2.2d:%2.2d %s' % (
                        y,m,d,h,mn,s,t)
        else: return '%4.4d/%2.2d/%2.2d' % (y,m,d)

    def __cmp__(self,obj):
        """Compare a DateTime with another DateTime object, or
           a float such as those returned by time.time().

           NOTE: __cmp__ support is provided for backward 
           compatibility only, and mixing DateTimes with
           ExtensionClasses could cause __cmp__ to break.
           You should use the methods lessThan, greaterThan,
           lessThanEqualTo, greaterThanEqualTo, equalTo and
           notEqualTo to avoid potential problems later!!"""
        try:                   return cmp(self._d,obj._d)
        except AttributeError: return cmp(self._t,obj)

    def __hash__(self):
        """Compute a hash value for a DateTime"""
        return int(((self._year%100*12+self._month)*31+
                     self._day+self.time)*100)

    def __int__(self):
        """Convert to an integer number of seconds since the epoch (gmt)"""
        return int(self._t)

    def __long__(self):
        """Convert to a long-int number of seconds since the epoch (gmt)"""
        return long(self._t)

    def __float__(self):
        """Convert to floating-point number of seconds since the epoch (gmt)"""
        return float(self._t)


class strftimeFormatter:

    def __init__(self, dt, format):
        self._dt=dt
        self._f=format

    def __call__(self): return self._dt.strftime(self._f)


# Module methods
def Timezones():
    """Return the list of recognized timezone names"""
    return _cache._zlst
