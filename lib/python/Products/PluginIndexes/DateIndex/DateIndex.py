##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""$Id: DateIndex.py,v 1.10 2003/01/23 17:46:19 andreasjung Exp $ """

from DateTime.DateTime import DateTime
from Products.PluginIndexes import PluggableIndex
from Products.PluginIndexes.common.UnIndex import UnIndex
from Products.PluginIndexes.common.util import parseIndexRequest
from types import StringType, FloatType, IntType

from Globals import DTMLFile
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.IIBTree import IISet, union, intersection, multiunion
import time

_marker = []


class DateIndex(UnIndex):
    """ Index for Dates """

    __implements__ = (PluggableIndex.UniqueValueIndex,
                      PluggableIndex.SortIndex)

    meta_type = 'DateIndex'
    query_options = ['query', 'range']

    manage = manage_main = DTMLFile( 'dtml/manageDateIndex', globals() )
    manage_main._setName( 'manage_main' )
    manage_options = ( { 'label' : 'Settings'
                       , 'action' : 'manage_main'
                       },
                     )

    def clear( self ):
        """ Complete reset """
        self._index = IOBTree()
        self._unindex = OIBTree()


    def index_object( self, documentId, obj, threshold=None ):
        """index an object, normalizing the indexed value to an integer

           o Normalized value has granularity of one minute.

           o Objects which have 'None' as indexed value are *omitted*,
             by design.
        """
        returnStatus = 0

        try:
            date_attr = getattr( obj, self.id )
            if callable( date_attr ):
                date_attr = date_attr()

            ConvertedDate = self._convert( value=date_attr, default=_marker )
        except AttributeError:
            ConvertedDate = _marker

        oldConvertedDate = self._unindex.get( documentId, _marker )

        if ConvertedDate != oldConvertedDate:
            if oldConvertedDate is not _marker:
                self.removeForwardIndexEntry(oldConvertedDate, documentId)

            if ConvertedDate is not _marker:
                self.insertForwardIndexEntry( ConvertedDate, documentId )
                self._unindex[documentId] = ConvertedDate

            returnStatus = 1

        return returnStatus


    def _apply_index( self, request, cid='', type=type ):
        """Apply the index to query parameters given in the argument

        Normalize the 'query' arguments into integer values at minute
        precision before querying.
        """
        record = parseIndexRequest( request, self.id, self.query_options )
        if record.keys == None:
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

            #for k, set in setlist:
                #if type(set) is IntType:
                    #set = IISet((set,))
                #r = set_func(r, set)
            # XXX: Use multiunion!
            r = multiunion(setlist)

        else: # not a range search
            for key in keys:
                set = index.get(key, None)
                if set is not None:
                    if type(set) is IntType:
                        set = IISet((set,))
                    r = set_func(r, set)

        if type(r) is IntType:
            r = IISet((r,))

        if r is None:
            return IISet(), (self.id,)
        else:
            return r, (self.id,)


    def _convert( self, value, default=None ):
        """Convert Date/Time value to our internal representation"""
        if isinstance( value, DateTime ):
            t_tup = value.parts()
        elif type( value ) in (FloatType, IntType):
            t_tup = time.gmtime( value )
        elif type( value ) is StringType:
            t_obj = DateTime( value )
            t_tup = t_obj.parts()
        else:
            return default

        yr = t_tup[0]
        mo = t_tup[1]
        dy = t_tup[2]
        hr = t_tup[3]
        mn = t_tup[4]

        t_val = ( ( ( ( yr * 12 + mo ) * 31 + dy ) * 24 + hr ) * 60 + mn )

        try:
            # t_val must be IntType, not LongType
            return int(t_val)
        except OverflowError:
            raise OverflowError, (
                "%s is not within the range of indexable dates (index: %s)"
                % (value, self.id))


manage_addDateIndexForm = DTMLFile( 'dtml/addDateIndex', globals() )

def manage_addDateIndex( self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a Date index"""
    return self.manage_addIndex(id, 'DateIndex', extra=None, \
                    REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
