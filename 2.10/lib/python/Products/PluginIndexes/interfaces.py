##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""PluginIndexes z3 interfaces.

$Id$
"""

from zope.interface import Interface
from zope.schema import Bool


class IPluggableIndex(Interface):

    def getId():
        """Return Id of index."""

    def getEntryForObject(documentId, default=None):
        """Get all information contained for 'documentId'."""

    def getIndexSourceNames():
        """Get a sequence of attribute names that are indexed by the index.
        """

    def index_object(documentId, obj, threshold=None):
        """Index an object.

        'documentId' is the integer ID of the document.
        'obj' is the object to be indexed.
        'threshold' is the number of words to process between committing
        subtransactions.  If None, subtransactions are disabled.
        """

    def unindex_object(documentId):
        """Remove the documentId from the index."""

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

    def numObjects():
        """Return the number of indexed objects"""

# XXX: not implemented by TextIndex and TopicIndex
#    def indexSize():
#        """Return the size of the index in terms of distinct values"""

    def clear():
        """Empty the index"""


class IUniqueValueIndex(IPluggableIndex):
    """An index which can return lists of unique values contained in it"""

    def hasUniqueValuesFor(name):
        """Return true if the index can return the unique values for name"""

    def uniqueValues(name=None, withLengths=0):
        """Return the unique values for name.

        If 'withLengths' is true, returns a sequence of tuples of
        (value, length)."""


class ISortIndex(IPluggableIndex):
    """An index which may be used to sort a set of document ids"""

    def keyForDocument(documentId):
        """Return the sort key that cooresponds to the specified document id

        This method is no longer used by ZCatalog, but is left for backwards
        compatibility."""

    def documentToKeyMap():
        """Return an object that supports __getitem__ and may be used to quickly
        lookup the sort key given a document id"""


class IDateIndex(Interface):

    """Index for dates.
    """

    index_naive_time_as_local = Bool(title=u'Index naive time as local?')


class IDateRangeIndex(Interface):

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

    def getSinceField():
        """Get the name of the attribute indexed as start date.
        """

    def getUntilField():
        """Get the name of the attribute indexed as end date.
        """


class IPathIndex(Interface):

    """Index for paths returned by getPhysicalPath.

    A path index stores all path components of the physical path of an object.

    Internal datastructure:

    - a physical path of an object is split into its components

    - every component is kept as a  key of a OOBTree in self._indexes

    - the value is a mapping 'level of the path component' to
      'all docids with this path component on this level'
    """


class IVocabulary(Interface):

    """A Vocabulary is a user-managable realization of a Lexicon object.
    """


class ITextIndex(Interface):

    """Full-text index.

    There is a ZCatalog UML model that sheds some light on what is
    going on here.  '_index' is a BTree which maps word ids to mapping
    from document id to score.  Something like:

      {'bob' : {1 : 5, 2 : 3, 42 : 9}}
      {'uncle' : {1 : 1}}

    The '_unindex' attribute is a mapping from document id to word
    ids.  This mapping allows the catalog to unindex an object:

      {42 : ('bob', 'is', 'your', 'uncle')

    This isn't exactly how things are represented in memory, many
    optimizations happen along the way.
    """

    def getLexicon(vocab_id=None):
        """Get the Lexicon in use.
        """


class IFilteredSet(Interface):
    """A pre-calculated result list based on an expression.
    """

    def getExpression():
        """Get the expression.
        """

    def getIds():
        """Get the IDs of all objects for which the expression is True.
        """

    def setExpression(expr):
        """Set the expression.
        """


class ITopicIndex(Interface):

    """A TopicIndex maintains a set of FilteredSet objects.

    Every FilteredSet object consists of an expression and and IISet with all
    Ids of indexed objects that eval with this expression to 1.
    """

    def addFilteredSet(filter_id, typeFilteredSet, expr):
        """Add a FilteredSet object.
        """

    def delFilteredSet(filter_id):
        """Delete the FilteredSet object specified by 'filter_id'.
        """

    def clearFilteredSet(filter_id):
        """Clear the FilteredSet object specified by 'filter_id'.
        """
