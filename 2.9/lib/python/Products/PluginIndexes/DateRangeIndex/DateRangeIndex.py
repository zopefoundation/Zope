##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Date range index.

$Id$
"""

import os

from AccessControl import ClassSecurityInfo
from BTrees.IIBTree import IISet, IITreeSet, union, intersection, multiunion
from BTrees.IOBTree import IOBTree
import BTrees.Length
from DateTime.DateTime import DateTime
from Globals import package_home, DTMLFile, InitializeClass
from zope.interface import implements

from Products.PluginIndexes.common import safe_callable
from Products.PluginIndexes.common.UnIndex import UnIndex
from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.interfaces import IDateRangeIndex

_dtmldir = os.path.join( package_home( globals() ), 'dtml' )

VIEW_PERMISSION         = 'View'
INDEX_MGMT_PERMISSION   = 'Manage ZCatalogIndex Entries'


class DateRangeIndex(UnIndex):

    """Index for date ranges, such as the "effective-expiration" range in CMF.

    Any object may return None for either the start or the end date: for the
    start date, this should be the logical equivalent of "since the beginning
    of time"; for the end date, "until the end of time".

    Therefore, divide the space of indexed objects into four containers:

    - Objects which always match (i.e., they returned None for both);

    - Objects which match after a given time (i.e., they returned None for the
      end date);

    - Objects which match until a given time (i.e., they returned None for the
      start date);

    - Objects which match only during a specific interval.
    """

    __implements__ = UnIndex.__implements__
    implements(IDateRangeIndex)

    security = ClassSecurityInfo()

    meta_type = "DateRangeIndex"

    manage_options= ( { 'label'     : 'Properties'
                      , 'action'    : 'manage_indexProperties'
                      }
                    ,
                    )

    query_options = ['query']

    since_field = until_field = None

    def __init__(self, id, since_field=None, until_field=None,
            caller=None, extra=None):

        if extra:
            since_field = extra.since_field
            until_field = extra.until_field

        self._setId(id)
        self._edit(since_field, until_field)
        self.clear()

    security.declareProtected(VIEW_PERMISSION, 'getSinceField')
    def getSinceField(self):
        """Get the name of the attribute indexed as start date.
        """
        return self._since_field

    security.declareProtected(VIEW_PERMISSION, 'getUntilField')
    def getUntilField(self):
        """Get the name of the attribute indexed as end date.
        """
        return self._until_field

    manage_indexProperties = DTMLFile( 'manageDateRangeIndex', _dtmldir )

    security.declareProtected(INDEX_MGMT_PERMISSION, 'manage_edit')
    def manage_edit( self, since_field, until_field, REQUEST ):
        """
        """
        self._edit( since_field, until_field )
        REQUEST[ 'RESPONSE' ].redirect( '%s/manage_main'
                                        '?manage_tabs_message=Updated'
                                      % REQUEST.get('URL2')
                                      )

    security.declarePrivate('_edit')
    def _edit( self, since_field, until_field ):
        """
            Update the fields used to compute the range.
        """
        self._since_field = since_field
        self._until_field = until_field

    security.declareProtected(INDEX_MGMT_PERMISSION, 'clear')
    def clear( self ):
        """
            Start over fresh.
        """
        self._always        = IITreeSet()
        self._since_only    = IOBTree()
        self._until_only    = IOBTree()
        self._since         = IOBTree()
        self._until         = IOBTree()
        self._unindex       = IOBTree() # 'datum' will be a tuple of date ints
        self._length        = BTrees.Length.Length()

    #
    #   PluggableIndexInterface implementation (XXX inherit assertions?)
    #
    def getEntryForObject( self, documentId, default=None ):
        """
            Get all information contained for the specific object
            identified by 'documentId'.  Return 'default' if not found.
        """
        return self._unindex.get( documentId, default )

    def index_object( self, documentId, obj, threshold=None ):
        """
            Index an object:

             - 'documentId' is the integer ID of the document

             - 'obj' is the object to be indexed

             - ignore threshold
        """
        if self._since_field is None:
            return 0

        since = getattr( obj, self._since_field, None )
        if safe_callable( since ):
            since = since()
        since = self._convertDateTime( since )

        until = getattr( obj, self._until_field, None )
        if safe_callable( until ):
            until = until()
        until = self._convertDateTime( until )

        datum = ( since, until )

        old_datum = self._unindex.get( documentId, None )
        if datum == old_datum: # No change?  bail out!
            return 0

        if old_datum is not None:
            old_since, old_until = old_datum
            self._removeForwardIndexEntry( old_since, old_until, documentId )

        self._insertForwardIndexEntry( since, until, documentId )
        self._unindex[ documentId ] = datum

        return 1

    def unindex_object( self, documentId ):
        """
            Remove the object corresponding to 'documentId' from the index.
        """
        datum = self._unindex.get( documentId, None )

        if datum is None:
            return

        since, until = datum

        self._removeForwardIndexEntry( since, until, documentId )
        del self._unindex[ documentId ]

    def uniqueValues( self, name=None, withLengths=0 ):
        """
            Return a list of unique values for 'name'.

            If 'withLengths' is true, return a sequence of tuples, in
            the form '( value, length )'.
        """
        if not name in ( self._since_field, self._until_field ):
            return []

        if name == self._since_field:

            t1 = self._since
            t2 = self._since_only

        else:

            t1 = self._until
            t2 = self._until_only

        result = []
        IntType = type( 0 )

        if not withLengths:

            result.extend( t1.keys() )
            result.extend( t2.keys() )

        else:

            for key in t1.keys():
                set = t1[ key ]
                if type( set ) is IntType:
                    length = 1
                else:
                    length = len( set )
                result.append( ( key, length) )

            for key in t2.keys():
                set = t2[ key ]
                if type( set ) is IntType:
                    length = 1
                else:
                    length = len( set )
                result.append( ( key, length) )

        return tuple( result )

    def _apply_index( self, request, cid='' ):
        """
            Apply the index to query parameters given in 'request', which
            should be a mapping object.

            If the request does not contain the needed parametrs, then
            return None.

            If the request contains a parameter with the name of the
            column + "_usage", snif for information on how to handle
            applying the index.

            Otherwise return two objects.  The first object is a ResultSet
            containing the record numbers of the matching records.  The
            second object is a tuple containing the names of all data fields
            used.
        """
        record = parseIndexRequest( request, self.getId() )
        if record.keys is None:
            return None

        term        = self._convertDateTime( record.keys[0] )

        #
        #   Aggregate sets for each bucket separately, to avoid
        #   large-small union penalties.
        #
        #until_only  = IISet()
        #map( until_only.update, self._until_only.values( term ) )
        # XXX use multi-union
        until_only = multiunion( self._until_only.values( term ) )

        #since_only  = IISet()
        #map( since_only.update, self._since_only.values( None, term ) )
        # XXX use multi-union
        since_only = multiunion( self._since_only.values( None, term ) )

        #until       = IISet()
        #map( until.update, self._until.values( term ) )
        # XXX use multi-union
        until = multiunion( self._until.values( term ) )

        #since       = IISet()
        #map( since.update, self._since.values( None, term ) )
        # XXX use multi-union
        since = multiunion( self._since.values( None, term ) )

        bounded     = intersection( until, since )

        #   Merge from smallest to largest.
        #result      = union( self._always, until_only )
        result      = union( bounded, until_only )
        result      = union( result, since_only )
        #result      = union( result, bounded )
        result      = union( result, self._always )

        return result, ( self._since_field, self._until_field )

    #
    #   ZCatalog needs this, although it isn't (yet) part of the interface.
    #
    security.declareProtected(VIEW_PERMISSION , 'numObjects')
    def numObjects( self ):
        """ """
        return len( self._unindex )

    def indexSize(self):
        """ """
        return len(self)

    #
    #   Helper functions.
    #
    def _insertForwardIndexEntry( self, since, until, documentId ):
        """
            Insert 'documentId' into the appropriate set based on
            'datum'.
        """
        if since is None and until is None:

            self._always.insert( documentId )

        elif since is None:

            set = self._until_only.get( until, None )
            if set is None:
                set = self._until_only[ until ] = IISet()  # XXX: Store an int?
            set.insert( documentId )

        elif until is None:

            set = self._since_only.get( since, None )
            if set is None:
                set = self._since_only[ since ] = IISet()  # XXX: Store an int?
            set.insert( documentId )

        else:

            set = self._since.get( since, None )
            if set is None:
                set = self._since[ since ] = IISet()   # XXX: Store an int?
            set.insert( documentId )

            set = self._until.get( until, None )
            if set is None:
                set = self._until[ until ] = IISet() # XXX: Store an int?
            set.insert( documentId )

    def _removeForwardIndexEntry( self, since, until, documentId ):
        """
            Remove 'documentId' from the appropriate set based on
            'datum'.
        """
        if since is None and until is None:

            self._always.remove( documentId )

        elif since is None:

            set = self._until_only.get( until, None )
            if set is not None:

                set.remove( documentId )

                if not set:
                    del self._until_only[ until ]

        elif until is None:

            set = self._since_only.get( since, None )
            if set is not None:

                set.remove( documentId )

                if not set:
                    del self._since_only[ since ]

        else:

            set = self._since.get( since, None )
            if set is not None:
                set.remove( documentId )

                if not set:
                    del self._since[ since ]

            set = self._until.get( until, None )
            if set is not None:
                set.remove( documentId )

                if not set:
                    del self._until[ until ]

    def _convertDateTime( self, value ):
        if value is None:
            return value
        if type( value ) == type( '' ):
            dt_obj = DateTime( value )
            value = dt_obj.millis() / 1000 / 60 # flatten to minutes
        if isinstance( value, DateTime ):
            value = value.millis() / 1000 / 60 # flatten to minutes
        result = int( value )
        if isinstance(result, long): # this won't work (Python 2.3)
            raise OverflowError( '%s is not within the range of dates allowed'
                              'by a DateRangeIndex' % value)
        return result

InitializeClass( DateRangeIndex )

manage_addDateRangeIndexForm = DTMLFile( 'addDateRangeIndex', _dtmldir )

def manage_addDateRangeIndex(self, id, extra=None,
        REQUEST=None, RESPONSE=None, URL3=None):
    """
        Add a date range index to the catalog, using the incredibly icky
        double-indirection-which-hides-NOTHING.
    """
    return self.manage_addIndex(id, 'DateRangeIndex', extra,
        REQUEST, RESPONSE, URL3)
