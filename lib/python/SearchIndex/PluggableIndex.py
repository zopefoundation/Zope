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

"""Pluggable Index Base Class """
__version__='$Revision: 1.3 $'[11:-2]

import Interface


class PluggableIndex:

    """Base pluggable index class"""


    def getEntryForObject(self, documentId, default=None):
        """Get all information contained for a specific object by documentId"""
        pass

    def index_object(self, documentId, obj, threshold=None):
        """Index an object:

           'documentId' is the integer ID of the document

           'obj' is the object to be indexed

           'threshold' is the number of words to process between committing
           subtransactions.  If None, subtransactions are disabled"""

        pass

    def unindex_object(self, documentId):
        """Remove the documentId from the index"""
        pass


    def uniqueValues(self, name=None, withLengths=0):
        """Returns the unique values for name.

        If 'withLengths' is true, returns a sequence of tuples of
        (value, length)"""

        pass

    def _apply_index(self, request, cid=''):
        """Apply the index to query parameters given in the argument, request.

        The argument should be a mapping object.

        If the request does not contain the needed parametrs, then None is
        returned.

        If the request contains a parameter with the name of the column
        + "_usage", it is sniffed for information on how to handle applying
        the index.

        Otherwise two objects are returned.  The first object is a ResultSet
        containing the record numbers of the matching records.  The second
        object is a tuple containing the names of all data fields used."""

        pass

PluggableIndexInterface = Interface.impliedInterface(PluggableIndex)

PluggableIndex.__implements__ = PluggableIndexInterface
