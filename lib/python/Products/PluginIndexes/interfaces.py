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


# create IPluggableIndex, IUniqueValueIndex, ISortIndex
from Products.Five.fiveconfigure import createZope2Bridge
from common.PluggableIndex import PluggableIndexInterface
from common.PluggableIndex import SortIndex
from common.PluggableIndex import UniqueValueIndex
import interfaces

createZope2Bridge(PluggableIndexInterface, interfaces, 'IPluggableIndex')
createZope2Bridge(SortIndex, interfaces, 'ISortIndex')
createZope2Bridge(UniqueValueIndex, interfaces, 'IUniqueValueIndex')

del createZope2Bridge
del PluggableIndexInterface
del SortIndex
del UniqueValueIndex
del interfaces


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
