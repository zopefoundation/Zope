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


class DateTime:

    """

    The DateTime object provides an interface for working with dates
    and times in various formats.  DateTime also provides methods for
    calendar operations, date and time arithmetic and formatting.

   DateTime objects represent instants in time and provide
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
    modify the current object.

    Return a new date-time object

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
        sixth arguments specify a time in hours, minutes, and
        seconds; hours and minutes should be positive integers
        and seconds is a positive floating point value, all of
        these default to zero if not given. An optional string may
        be given as the final argument to indicate timezone (the
        effect of this is as if you had taken the value of time.time()
        at that time on a machine in the specified timezone).

    If a string argument passed to the DateTime constructor cannot be
    parsed, it will raise DateTime.SyntaxError. Invalid date, time, or
    timezone components will raise a DateTime.DateTimeError. 

    The module function Timezones() will return a list of the 
    timezones recognized by the DateTime module. Recognition of 
    timezone names is case-insensitive.

    """


    def timeTime(self):
        """

        Return the date/time as a floating-point number in UTC, in the
        format used by the python time module.  Note that it is
        possible to create date/time values with DateTime that have no
        meaningful value to the time module.

        """

    def toZone(self, z):
        """

        Return a DateTime with the value as the current object,
        represented in the indicated timezone.

        """

    def isFuture(self):
        """

        Return true if this object represents a date/time later than
        the time of the call

        """

    def isPast(self):
        """

        Return true if this object represents a date/time earlier than
        the time of the call

        """

    def isCurrentYear(self):
        """

        Return true if this object represents a date/time that falls
        within the current year, in the context of this object\'s
        timezone representation

        """

    def isCurrentMonth(self):
        """

        Return true if this object represents a date/time that falls
        within the current month, in the context of this object\'s
        timezone representation

        """

    def isCurrentDay(self):
        """

        Return true if this object represents a date/time that falls
        within the current day, in the context of this object\'s
        timezone representation

        """

    def isCurrentHour(self):
        """

        Return true if this object represents a date/time that falls
        within the current hour, in the context of this object\'s
        timezone representation

        """

    def isCurrentMinute(self):
        """

        Return true if this object represents a date/time that falls
        within the current minute, in the context of this object\'s
        timezone representation

        """

    def earliestTime(self):
        """

        Return a new DateTime object that represents the earliest
        possible time (in whole seconds) that still falls within the
        current object\'s day, in the object\'s timezone context

        """

    def latestTime(self):
        """

        Return a new DateTime object that represents the latest
        possible time (in whole seconds) that still falls within the
        current object\'s day, in the object\'s timezone context

        """

    def greaterThan(self,t):
        """

        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time greater than the specified DateTime or time module
        style time.  Revised to give more correct results through
        comparison of long integer milliseconds.

        """

    def greaterThanEqualTo(self,t):
        """

        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time greater than or equal to the specified DateTime or
        time module style time.  Revised to give more correct results
        through comparison of long integer milliseconds.

        """

    def equalTo(self,t):
        """

        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time equal to the specified DateTime or time module style
        time.  Revised to give more correct results through comparison
        of long integer milliseconds.

        """

    def notEqualTo(self,t):
        """

        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time not equal to the specified DateTime or time module
        style time.  Revised to give more correct results through
        comparison of long integer milliseconds.

        """

    def lessThan(self,t):
        """

        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time less than the specified DateTime or time module
        style time.  Revised to give more correct results through
        comparison of long integer milliseconds.

        """

    def lessThanEqualTo(self,t):
        """

        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time less than or equal to the specified DateTime or time
        module style time.  Revised to give more correct results
        through comparison of long integer milliseconds.

        """

    def isLeapYear(self):
        """

        Return true if the current year (in the context of the
        object\'s timezone) is a leap year

        """

    def dayOfYear(self):
        """

        Return the day of the year, in context of the timezone
        representation of the object

        """

    # Component access
    def parts(self):
        """

        Return a tuple containing the calendar year, month, day, hour,
        minute second and timezone of the object

        """

    def timezone(self):
        """

        Return the timezone in which the object is represented.

        """

    def year(self):
        """

        Return the calendar year of the object

        """


    def month(self):
        """

        Return the month of the object as an integer

        """


    def Month(self):
        """

        Return the full month name

        """


    def aMonth(self):
        """

        Return the abreviated month name.

        """


    def Mon(self):
        """

        Compatibility: see aMonth

        """


    def pMonth(self):
        """

        Return the abreviated (with period) month name.

        """


    def Mon_(self):
        """

        Compatibility: see pMonth

        """


    def day(self):
        """

        Return the integer day

        """


    def Day(self): 
        """

        Return the full name of the day of the week

        """


    def DayOfWeek(self):
        """

        Compatibility: see Day

        """


    def aDay(self):
        """

        Return the abreviated name of the day of the week

        """


    def pDay(self):
        """

        Return the abreviated (with period) name of the day of the
        week


        """


    def Day_(self):
        """

        Compatibility: see pDay

        """


    def dow(self):
        """

        Return the integer day of the week, where sunday is 0

        """


    def dow_1(self):
        """

        Return the integer day of the week, where sunday is 1

        """


    def h_12(self):
        """

        Return the 12-hour clock representation of the hour

        """


    def h_24(self):
        """

        Return the 24-hour clock representation of the hour

        """


    def ampm(self):
        """

        Return the appropriate time modifier (am or pm)

        """


    def hour(self):
        """

        Return the 24-hour clock representation of the hour

        """


    def minute(self):
        """

        Return the minute

        """


    def second(self):
        """

        Return the second

        """


    def millis(self):
        """

        Return the millisecond since the epoch in GMT.

        """

    def strftime(self, format):
        """

        Return date time string formatted according to 'format'

        """

    # General formats from previous DateTime
    def Date(self):
        """

        Return the date string for the object.

        """

    def Time(self):
        """

        Return the time string for an object to the nearest second.

        """

    def TimeMinutes(self): 
        """

        Return the time string for an object not showing seconds.

        """

    def AMPM(self):
        """

        Return the time string for an object to the nearest second.

        """


    def AMPMMinutes(self):
        """

        Return the time string for an object not showing seconds.

        """

    def PreciseTime(self):
        """

        Return the time string for the object.

        """

    def PreciseAMPM(self):
        """Return the time string for the object."""

    def yy(self):
        """Return calendar year as a 2 digit string"""

    def mm(self):
        """Return month as a 2 digit string"""

    def dd(self):
        """Return day as a 2 digit string"""

    def rfc822(self):
        """Return the date in RFC 822 format"""

    # New formats
    def fCommon(self):
        """Return a string representing the object\'s value
           in the format: March 1, 1997 1:45 pm"""

    def fCommonZ(self):
        """Return a string representing the object\'s value
           in the format: March 1, 1997 1:45 pm US/Eastern"""

    def aCommon(self):
        """Return a string representing the object\'s value
           in the format: Mar 1, 1997 1:45 pm"""

    def aCommonZ(self):
        """Return a string representing the object\'s value
           in the format: Mar 1, 1997 1:45 pm US/Eastern"""

    def pCommon(self):
        """Return a string representing the object\'s value
           in the format: Mar. 1, 1997 1:45 pm"""

    def pCommonZ(self):
        """Return a string representing the object\'s value
           in the format: Mar. 1, 1997 1:45 pm US/Eastern"""


    def ISO(self):
        """Return the object in ISO standard format

        Dates are output as: YYYY-MM-DD HH:MM:SS
        """

    def HTML4(self):
        """Return the object in the format used in the HTML4.0 specification,
        one of the standard forms in ISO8601.  See
               http://www.w3.org/TR/NOTE-datetime

        Dates are output as: YYYY-MM-DDTHH:MM:SSZ
           T, Z are literal characters.
           The time is in UTC.
        """















