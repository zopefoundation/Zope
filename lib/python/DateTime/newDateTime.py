from mx.DateTime import DateTime           as mxDateTime
from mx.DateTime import DateTimeFrom       as mxDateTimeFrom
from mx.DateTime import Time               as mxTime
from mx.DateTime import DateFromTicks      as mxDateFromTicks 
from mx.DateTime import TimestampFromTicks as mxTimestampFromTicks 
from mx.DateTime import ARPA
from mx.DateTime import now
from mx.DateTime import strptime
from mx.DateTime.Timezone import zonetable

from newDateTimeZone import _TimeZoneMapper

import time,types
from time import localtime


class DateTime:

    __roles__=None
    __allow_access_to_unprotected_subobjects__=1


    def __init__(self,*args):
        if len(args) == 0 or (len(args) > 0 and args[0] == None):
            self.dt = mxTimestampFromTicks(time.time())
            
        elif ( type(args[0]) is types.FloatType or
               type(args[0]) is types.IntType and len(args) == 1):
            self.dt = mxTimestampFromTicks(args[0])

        elif type(args[0]) is types.StringType and len(args) == 1:
            self.dt = mxDateTimeFrom(args[0])

        elif ( type(args[0]) is types.StringType and
               type(args[0]) is types.StringType and len(args) == 2):
            self.dt = strptime(args[0], args[1])
            
        else:
            self.dt = apply(mxDateTime,args)

        for x in dir(self.dt):
            setattr(self,x,getattr(self.dt,x))


    def strftime(self,fmt): return self.dt.strftime(fmt)

    def ISO(self):          return self.dt.strftime('%04Y-%02m-%02d %02H:%02M:%02S')
    def HTML4(self):        return self.dt.strftime('%04Y-%02m-%02dT%02H:%02M:%02S%Z')
    def rfc822(self):       return ARPA.strGMT(self.dt)

    def dow(self):          return self.dt.day_of_week
    def dayOfYear(self):    return self.dt.day_of_year

    def yy(self):           return self.strftime('%02y')
    def mm(self):           return self.strftime('%02m')
    def dd(self):           return self.strftime('%02d')

    def h_24(self):         return self.strftime('%02H')
    def h_12(self):         return self.strftime('%02I')
    def ampm(self):         return self.strftime('%P')

    def hour(self):         return self.dt.hour
    def minute(self):       return self.dt.minute
    def second(self):       return int(self.dt.second)
    def millis(self):       return self.dt.second - int(self.dt.second)
    def day(self):          return self.dt.day
    def month(self):        return self.dt.month
    def year(self):         return self.dt.year
    def timezone(self):     return self.dt.timezone

    def Day(self):          return self.strftime('%A')
    def DayOfWeek(self):    return self.Day()
    def aDay(self):         return self.strftime('%a')
    def pDay(self):         return self.strftime('%a.')
    def Day_(self):         return self.pDay()

    def dow(self):          return self.strftime('%w')
    def dow_1(self):        return self.dow()+1

    def Month(self):        return self.strftime('%B')
    def aMonth(self):       return self.strftime('%b')
    def Mon(self):          return self.aMonth()
    def pMonth(self):       return self.strftime('%b.')
    def Mon_(self):         return self.pMonth()
    
    def isLeapYear(self):   return self.dt.is_leapyear

    def timeTime(self):     return self.dt.gmticks()
    def toZone(self, z):    return self.dt + mxTime(zonetable[z])
    def isFuture(self):     return self.dt > now()
    def isPast(self):       return self.dt < now()

    def isCurrentYear(self):   return self.dt.year == now().year
    def isCurrentMonth(self):  return self.isCurrentYear() and self.dt.month == now().month
    def isCurrentDay(self):    return self.date() and now().date()
    def isCurrentHour(self):   return self.isCurrentDay() and self.dt.hour == now.hour
    def isCurrentMinute(self): return self.isCurrentHour() and self.dt.minute == now.minute

    def earliestTime(self):    return mxDateTime(self.dt.year, self.dt.month, self.dt.day)
    def latestTime(self):      return mxDateTime(self.dt.year, self.dt.month, self.dt.day, 23, 59, 59)

    def greaterThan(self,t):        return self.dt >  t.dt
    def greaterThanEqualTo(self,t): return self.dt >= t.dt
    def equalTo(self,t):            return self.dt == t.dt
    def notEqualTo(self,t):         return self.dt != t.dt
    def lessThan(self,t):           return self.dt <  t.dt
    def lessThanEqualTo(self,t):    return self.dt <= t.dt

    def parts(self):        return self.dt.year, self.dt.month, self.dt.day, self.dt.hour, \
                                   self.dt.minute, self.dt.second, self.dt.timezone
    def localZone(self, ltm=None):  pass


    def Date(self):         return self.strftime('%Y/%m/%d')
    def Time(self):         return self.strftime('%H:%M:%S')
    def TimeMinutes(self):  return self.strftime('%H:%M')
    def AMPM(self):         return self.strftime('%I:%M:%S %P')
    def AMPMMinutes(self):  return self.strftime('%I:%M %P')
    def PreciseTime(self):  return self.strftime('%H:%M:') + '%06.3f' %(self.dt.second)
    def PreciseAMPM(self):  return self.strftime('%I:%M:') + '%06.3f' %(self.dt.second) + self.strftime(' %P')
                            
                            
    def fCommon(self):      return self.strftime('%B %d, %Y %l:%M %P')
    def fCommonZ(self):     return self.strftime('%B %d, %Y %l:%M %P ') + self.dt.timezone
    def aCommon(self):      return self.strftime('%b %d, %Y %l:%M %P')
    def aCommonZ(self):     return self.strftime('%b %d, %Y %l:%M %P ') + self.dt.timezone
    def pCommon(self):      return self.strftime('%b. %d, %Y %l:%M %P')
    def pCommonZ(self):     return self.strftime('%b. %d, %Y %l:%M %P ') + self.dt.timezone


    def __add__(self, other):       return self.dt + other
    __radd__ = __add__
    def __sub__(self, other):      return self.dt - other
    def __int__(self):             return int(self.dt.second)
    def __long__(self):            return long(self.dt.second)
    def __float__(self):           return self.dt.second

    def __cmp__(self, dateTime):
        try:                   return cmp(self.dt, dateTime.dt)
        except AttributeError: return cmp(self.dt.ticks(), dateTime)

    def __hash__(self):
        return int(((self.dt.year%100*12 + self._month)*31 +
                    self.dt.day+self.hour)*100)


    def __str__(self):      return str(self.dt)
    def __repr__(self):     return self.dt

    def __getattr__(self,fmt):
        if '%' in fmt:      return  strftimeFormater(self.dt,fmt)
        raise AttributeError,fmt


def Timezones():
    """Return the list of recognized timezone names"""
    return _TimeZoneMapper._zoneList


class strftimeFormater:

    def __init__(self,dt,fmt):
        self.dt     = dt
        self.fmt    = fmt

    def __call__(self,*args):
        return self.dt.strftime(self.fmt)
    

