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
__version__='$Revision: 1.7 $'[11:-2]

import Interface

class PluggableIndexInterface(Interface.Base):

    def getId():
        """Return Id of index."""

    def getEntryForObject(documentId, default=None):
        """Get all information contained for 'documentId'."""

    def index_object(documentId, obj, threshold=None):
        """Index an object.

        'documentId' is the integer ID of the document.
        'obj' is the object to be indexed.
        'threshold' is the number of words to process between committing
        subtransactions.  If None, subtransactions are disabled.
        """

    def unindex_object(documentId):
        """Remove the documentId from the index."""

    # XXX TextIndex does not implement uniqueValues().
    def uniqueValues(name=None, withLengths=0):
        """Returns the unique values for name.

        If 'withLengths' is true, returns a sequence of tuples of
        (value, length).
        """

    def _apply_index(request, cid=''):
        """Apply the index to query parameters given in 'request'.

        The argument should be a mapping object.

        If the request does not contain the needed parametrs, then
        None is returned.

        If the request contains a parameter with the name of the column
        + "_usage", it is sniffed for information on how to handle applying
        the index. (Note: this style or parameters is deprecated)

        If the request contains a parameter with the name of the
        column and this parameter is either a Record or a class
        instance then it is assumed that the parameters of this index
        are passed as attribute (Note: this is the recommended way to
        pass parameters since Zope 2.4)

        Otherwise two objects are returned.  The first object is a
        ResultSet containing the record numbers of the matching
        records.  The second object is a tuple containing the names of
        all data fields used.
        """
