##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
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
    to many major timezones, as well as the ability to create a
    DateTime object in the context of a given timezone.

    DateTime objects provide partial
    numerical behavior:

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

    A DateTime object always maintains its value as an absolute
    UTC time, and is represented in the context of some timezone
    based on the arguments used to create the object. A DateTime
    object's methods return values based on the timezone context.

    Note that in all cases the local machine timezone is used for
    representation if no timezone is specified.

    DateTimes may be created with from zero to
    seven arguments.

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
        recognized and unambiguous to a resident of North America is
        acceptable.(The reason for this qualification is that
        in North America, a date like: 2/1/1994 is interpreted
        as February 1, 1994, while in some parts of the world,
        it is interpreted as January 2, 1994.) A date/time
        string consists of two components, a date component and
        an optional time component, separated by one or more
        spaces. If the time component is omitted, 12:00am is
        assumed. Any recognized timezone name specified as the
        final element of the date/time string will be used for
        computing the date/time value. (If you create a DateTime
        with the string 'Mar 9, 1997 1:45pm US/Pacific', the
        value will essentially be the same as if you had captured
        time.time() at the specified date and time on a machine in
        that timezone)::

          e=DateTime("US/Eastern")
          # returns current date/time, represented in US/Eastern.

          x=DateTime("1997/3/9 1:45pm")
          # returns specified time, represented in local machine zone.

          y=DateTime("Mar 9, 1997 13:45:00")
          # y is equal to x


        The date component consists of year, month, and day
        values. The year value must be a one-, two-, or
        four-digit integer. If a one- or two-digit year is
        used, the year is assumed to be in the twentieth
        century. The month may be an integer, from 1 to 12, a
        month name, or a month abbreviation, where a period may
        optionally follow the abbreviation. The day must be an
        integer from 1 to the number of days in the month. The
        year, month, and day values may be separated by
        periods, hyphens, forward slashes, or spaces. Extra
        spaces are permitted around the delimiters. Year,
        month, and day values may be given in any order as long
        as it is possible to distinguish the components. If all
        three components are numbers that are less than 13,
        then a month-day-year ordering is assumed.

        The time component consists of hour, minute, and second
        values separated by colons.  The hour value must be an
        integer between 0 and 23 inclusively. The minute value
        must be an integer between 0 and 59 inclusively. The
        second value may be an integer value between 0 and
        59.999 inclusively. The second value or both the minute
        and second values may be omitted. The time may be
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
        in the given timezone.::

          import time
          t=time.time()

          now_east=DateTime(t,'US/Eastern')
          # Time t represented as US/Eastern

          now_west=DateTime(t,'US/Pacific')
          # Time t represented as US/Pacific

          # now_east == now_west
          # only their representations are different



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

        New in Zope 2.7:
        A new keyword parameter "datefmt" can be passed to the 
        constructor. If set to "international", the constructor
        is forced to treat ambigious dates as "days before month
        before year". This useful if you need to parse non-US
        dates in a reliable way

    If a string argument passed to the DateTime constructor cannot be
    parsed, it will raise DateTime.SyntaxError. Invalid date, time, or
    timezone components will raise a DateTime.DateTimeError.

    The module function Timezones() will return a list of the
    timezones recognized by the DateTime module. Recognition of
    timezone names is case-insensitive.

    """


    def timeTime():
        """
        Return the date/time as a floating-point number in UTC, in the
        format used by the python time module.  Note that it is
        possible to create date/time values with DateTime that have no
        meaningful value to the time module.

        Permission -- Always available
        """

    def toZone(z):
        """
        Return a DateTime with the value as the current object,
        represented in the indicated timezone.

        Permission -- Always available
        """

    def isFuture():
        """
        Return true if this object represents a date/time later than
        the time of the call

        Permission -- Always available
        """

    def isPast():
        """
        Return true if this object represents a date/time earlier than
        the time of the call

        Permission -- Always available
        """

    def isCurrentYear():
        """
        Return true if this object represents a date/time that falls
        within the current year, in the context of this object\'s
        timezone representation

        Permission -- Always available
        """

    def isCurrentMonth():
        """
        Return true if this object represents a date/time that falls
        within the current month, in the context of this object\'s
        timezone representation

        Permission -- Always available
        """

    def isCurrentDay():
        """
        Return true if this object represents a date/time that falls
        within the current day, in the context of this object\'s
        timezone representation

        Permission -- Always available
        """

    def isCurrentHour():
        """
        Return true if this object represents a date/time that falls
        within the current hour, in the context of this object\'s
        timezone representation

        Permission -- Always available
        """

    def isCurrentMinute():
        """
        Return true if this object represents a date/time that falls
        within the current minute, in the context of this object\'s
        timezone representation

        Permission -- Always available
        """

    def earliestTime():
        """
        Return a new DateTime object that represents the earliest
        possible time (in whole seconds) that still falls within the
        current object's day, in the object's timezone context

        Permission -- Always available
        """

    def latestTime():
        """
        Return a new DateTime object that represents the latest
        possible time (in whole seconds) that still falls within the
        current object's day, in the object's timezone context

        Permission -- Always available
        """

    def greaterThan(t):
        """
        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time greater than the specified DateTime or time module
        style time.  Revised to give more correct results through
        comparison of long integer milliseconds.

        Permission -- Always available
        """

    def greaterThanEqualTo(t):
        """
        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time greater than or equal to the specified DateTime or
        time module style time.  Revised to give more correct results
        through comparison of long integer milliseconds.

        Permission -- Always available
        """

    def equalTo(t):
        """
        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time equal to the specified DateTime or time module style
        time.  Revised to give more correct results through comparison
        of long integer milliseconds.

        Permission -- Always available
        """

    def notEqualTo(t):
        """
        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time not equal to the specified DateTime or time module
        style time.  Revised to give more correct results through
        comparison of long integer milliseconds.

        Permission -- Always available
        """

    def lessThan(t):
        """
        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time less than the specified DateTime or time module
        style time.  Revised to give more correct results through
        comparison of long integer milliseconds.

        Permission -- Always available
        """

    def lessThanEqualTo(t):
        """
        Compare this DateTime object to another DateTime object OR a
        floating point number such as that which is returned by the
        python time module. Returns true if the object represents a
        date/time less than or equal to the specified DateTime or time
        module style time.  Revised to give more correct results
        through comparison of long integer milliseconds.

        Permission -- Always available
        """

    def isLeapYear():
        """
        Return true if the current year (in the context of the
        object's timezone) is a leap year

        Permission -- Always available
        """

    def dayOfYear():
        """
        Return the day of the year, in context of the timezone
        representation of the object

        Permission -- Always available
        """

    # Component access
    def parts():
        """
        Return a tuple containing the calendar year, month, day, hour,
        minute second and timezone of the object

        Permission -- Always available
        """

    def timezone():
        """
        Return the timezone in which the object is represented.

        Permission -- Always available
        """

    def year():
        """
        Return the calendar year of the object

        Permission -- Always available
        """

    def month():
        """
        Return the month of the object as an integer

        Permission -- Always available
        """


    def Month():
        """
        Return the full month name

        Permission -- Always available
        """


    def aMonth():
        """
        Return the abbreviated month name.

        Permission -- Always available
        """


    def Mon():
        """
        Compatibility: see aMonth

        Permission -- Always available
        """


    def pMonth():
        """
        Return the abbreviated (with period) month name.

        Permission -- Always available
        """


    def Mon_():
        """
        Compatibility: see pMonth

        Permission -- Always available
        """


    def day():
        """
        Return the integer day

        Permission -- Always available
        """


    def Day():
        """
        Return the full name of the day of the week

        Permission -- Always available
        """


    def DayOfWeek():
        """
        Compatibility: see Day

        Permission -- Always available
        """


    def aDay():
        """
        Return the abbreviated name of the day of the week

        Permission -- Always available
        """

    def pDay():
        """
        Return the abbreviated (with period) name of the day of the
        week

        Permission -- Always available
        """

    def Day_():
        """
        Compatibility: see pDay

        Permission -- Always available
        """

    def dow():
        """
        Return the integer day of the week, where Sunday is 0

        Permission -- Always available
        """

    def dow_1():
        """
        Return the integer day of the week, where Sunday is 1

        Permission -- Always available
        """


    def h_12():
        """
        Return the 12-hour clock representation of the hour

        Permission -- Always available
        """


    def h_24():
        """
        Return the 24-hour clock representation of the hour

        Permission -- Always available
        """


    def ampm():
        """
        Return the appropriate time modifier (am or pm)

        Permission -- Always available
        """


    def hour():
        """
        Return the 24-hour clock representation of the hour

        Permission -- Always available
        """


    def minute():
        """
        Return the minute

        Permission -- Always available
        """


    def second():
        """
        Return the second

        Permission -- Always available
        """


    def millis():
        """
        Return the millisecond since the epoch in GMT.

        Permission -- Always available
        """

    def strftime(format):
        """

        Return date time string formatted according to 'format'

        See Python's
        "time.strftime":http://www.python.org/doc/current/lib/module-time.html
        function.
        """

    # General formats from previous DateTime
    def Date():
        """
        Return the date string for the object.

        Permission -- Always available
        """

    def Time():
        """
        Return the time string for an object to the nearest second.

        Permission -- Always available
        """

    def TimeMinutes():
        """
        Return the time string for an object not showing seconds.

        Permission -- Always available
        """

    def AMPM():
        """
        Return the time string for an object to the nearest second.

        Permission -- Always available
        """


    def AMPMMinutes():
        """
        Return the time string for an object not showing seconds.

        Permission -- Always available
        """

    def PreciseTime():
        """
        Return the time string for the object.

        Permission -- Always available
        """

    def PreciseAMPM():
        """
        Return the time string for the object.

        Permission -- Always available
        """

    def yy():
        """
        Return calendar year as a 2 digit string

        Permission -- Always available
        """

    def mm():
        """
        Return month as a 2 digit string

        Permission -- Always available
        """

    def dd():
        """
        Return day as a 2 digit string

        Permission -- Always available
        """

    def rfc822():
        """
        Return the date in RFC 822 format

        Permission -- Always available
        """

    # New formats
    def fCommon():
        """
        Return a string representing the object's value
        in the format: March 1, 1997 1:45 pm

        Permission -- Always available
        """

    def fCommonZ():
        """
        Return a string representing the object's value
        in the format: March 1, 1997 1:45 pm US/Eastern

        Permission -- Always available
        """

    def aCommon():
        """
        Return a string representing the object's value
        in the format: Mar 1, 1997 1:45 pm

        Permission -- Always available
        """

    def aCommonZ():
        """
        Return a string representing the object's value
        in the format: Mar 1, 1997 1:45 pm US/Eastern

        Permission -- Always available
        """

    def pCommon():
        """
        Return a string representing the object's value
        in the format: Mar. 1, 1997 1:45 pm

        Permission -- Always available
        """

    def pCommonZ():
        """
        Return a string representing the object's value
        in the format: Mar. 1, 1997 1:45 pm US/Eastern

        Permission -- Always available
        """


    def ISO():
        """
        Return the object in ISO standard format

        Dates are output as: YYYY-MM-DD HH:MM:SS

        Permission -- Always available
        """

    def HTML4():
        """
        Return the object in the format used in the HTML4.0 specification,
        one of the standard forms in ISO8601.

        See "HTML 4.0 Specification":http://www.w3.org/TR/NOTE-datetime

        Dates are output as: YYYY-MM-DDTHH:MM:SSZ
        T, Z are literal characters.
        The time is in UTC.

        Permission -- Always available
        """
