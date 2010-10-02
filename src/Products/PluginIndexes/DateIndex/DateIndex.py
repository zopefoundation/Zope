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
"""Date index.

$Id$
"""

import time
from logging import getLogger
from datetime import date, datetime
from datetime import tzinfo, timedelta

from App.special_dtml import DTMLFile
from BTrees.IIBTree import IISet
from BTrees.IIBTree import union
from BTrees.IIBTree import intersection
from BTrees.IIBTree import multiunion
from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from BTrees.OIBTree import OIBTree
from DateTime.DateTime import DateTime
from OFS.PropertyManager import PropertyManager
from ZODB.POSException import ConflictError
from zope.interface import implements

from Products.PluginIndexes.common import safe_callable
from Products.PluginIndexes.common.UnIndex import UnIndex
from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.interfaces import IDateIndex

LOG = getLogger('DateIndex')
_marker = []

###############################################################################
# copied from Python 2.3 datetime.tzinfo docs
# A class capturing the platform's idea of local time.

ZERO = timedelta(0)
STDOFFSET = timedelta(seconds = -time.timezone)
if time.daylight:
    DSTOFFSET = timedelta(seconds = -time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET
MAX32 = int(2**31 - 1)


class LocalTimezone(tzinfo):

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, -1)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0

Local = LocalTimezone()
###############################################################################


class DateIndex(UnIndex, PropertyManager):

    """Index for dates.
    """
    implements(IDateIndex)

    meta_type = 'DateIndex'
    query_options = ('query', 'range')

    index_naive_time_as_local = True # False means index as UTC
    _properties=({'id':'index_naive_time_as_local',
                  'type':'boolean',
                  'mode':'w'},)

    manage = manage_main = DTMLFile( 'dtml/manageDateIndex', globals() )
    manage_browse = DTMLFile('../dtml/browseIndex', globals())

    manage_main._setName( 'manage_main' )
    manage_options = ( { 'label' : 'Settings'
                       , 'action' : 'manage_main'
                       },
                       {'label': 'Browse',
                        'action': 'manage_browse',
                       },
                     ) + PropertyManager.manage_options

    def clear( self ):
        """ Complete reset """
        self._index = IOBTree()
        self._unindex = OIBTree()
        self._length = Length()

    def index_object( self, documentId, obj, threshold=None ):
        """index an object, normalizing the indexed value to an integer

           o Normalized value has granularity of one minute.

           o Objects which have 'None' as indexed value are *omitted*,
             by design.
        """
        returnStatus = 0

        try:
            date_attr = getattr( obj, self.id )
            if safe_callable( date_attr ):
                date_attr = date_attr()

            ConvertedDate = self._convert( value=date_attr, default=_marker )
        except AttributeError:
            ConvertedDate = _marker

        oldConvertedDate = self._unindex.get( documentId, _marker )

        if ConvertedDate != oldConvertedDate:
            if oldConvertedDate is not _marker:
                self.removeForwardIndexEntry(oldConvertedDate, documentId)
                if ConvertedDate is _marker:
                    try:
                        del self._unindex[documentId]
                    except ConflictError:
                        raise
                    except:
                        LOG.error("Should not happen: ConvertedDate was there,"
                                  " now it's not, for document with id %s" %
                                  documentId)

            if ConvertedDate is not _marker:
                self.insertForwardIndexEntry( ConvertedDate, documentId )
                self._unindex[documentId] = ConvertedDate

            returnStatus = 1

        return returnStatus

    def _apply_index(self, request):
        """Apply the index to query parameters given in the argument

        Normalize the 'query' arguments into integer values at minute
        precision before querying.
        """
        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys is None:
            return None

        keys = map( self._convert, record.keys )

        index = self._index
        r = None
        opr = None

        #experimental code for specifing the operator
        operator = record.get( 'operator', self.useOperator )
        if not operator in self.operators :
            raise RuntimeError, "operator not valid: %s" % operator

        # depending on the operator we use intersection or union
        if operator=="or":
            set_func = union
        else:
            set_func = intersection

        # range parameter
        range_arg = record.get('range',None)
        if range_arg:
            opr = "range"
            opr_args = []
            if range_arg.find("min") > -1:
                opr_args.append("min")
            if range_arg.find("max") > -1:
                opr_args.append("max")

        if record.get('usage',None):
            # see if any usage params are sent to field
            opr = record.usage.lower().split(':')
            opr, opr_args = opr[0], opr[1:]

        if opr=="range":   # range search
            if 'min' in opr_args:
                lo = min(keys)
            else:
                lo = None

            if 'max' in opr_args:
                hi = max(keys)
            else:
                hi = None

            if hi:
                setlist = index.values(lo,hi)
            else:
                setlist = index.values(lo)

            r = multiunion(setlist)

        else: # not a range search
            for key in keys:
                set = index.get(key, None)
                if set is not None:
                    if isinstance(set, int):
                        set = IISet((set,))
                    r = set_func(r, set)

        if isinstance(r, int):
            r = IISet((r,))

        if r is None:
            return IISet(), (self.id,)
        else:
            return r, (self.id,)

    def _convert( self, value, default=None ):
        """Convert Date/Time value to our internal representation"""
        # XXX: Code patched 20/May/2003 by Kiran Jonnalagadda to
        # convert dates to UTC first.
        if isinstance(value, DateTime):
            t_tup = value.toZone('UTC').parts()
        elif isinstance(value, (float, int)):
            t_tup = time.gmtime( value )
        elif isinstance(value, str) and value:
            t_obj = DateTime( value ).toZone('UTC')
            t_tup = t_obj.parts()
        elif isinstance(value, datetime):
            if self.index_naive_time_as_local and value.tzinfo is None:
                value = value.replace(tzinfo=Local)
            # else if tzinfo is None, naive time interpreted as UTC
            t_tup = value.utctimetuple()
        elif isinstance(value, date):
            t_tup = value.timetuple()
        else:
            return default

        yr = t_tup[0]
        mo = t_tup[1]
        dy = t_tup[2]
        hr = t_tup[3]
        mn = t_tup[4]

        t_val = ( ( ( ( yr * 12 + mo ) * 31 + dy ) * 24 + hr ) * 60 + mn )

        if t_val > MAX32:
            # t_val must be integer fitting in the 32bit range
            raise OverflowError(
                "%s is not within the range of indexable dates (index: %s)"
                % (value, self.id))

        return t_val


manage_addDateIndexForm = DTMLFile( 'dtml/addDateIndex', globals() )

def manage_addDateIndex( self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a Date index"""
    return self.manage_addIndex(id, 'DateIndex', extra=None, \
                    REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
