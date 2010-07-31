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
"""Filtered set.
"""

from logging import getLogger
import sys

from BTrees.IIBTree import IITreeSet
from Persistence import Persistent
from RestrictedPython.Eval import RestrictionCapableEval
from ZODB.POSException import ConflictError
from zope.interface import implements

from Products.PluginIndexes.interfaces import IFilteredSet

LOG = getLogger('Zope.TopicIndex.FilteredSet')


class FilteredSetBase(Persistent):
    # A pre-calculated result list based on an expression.

    implements(IFilteredSet)

    def __init__(self, id, expr):
        self.id   = id
        self.expr = expr
        self.clear()

    def clear(self):
        self.ids  = IITreeSet()

    def index_object(self, documentId, obj):
        raise RuntimeError,'index_object not defined'

    def unindex_object(self,documentId):
        try: self.ids.remove(documentId)
        except KeyError: pass

    def getId(self):
        return self.id

    def getExpression(self):
        # Get the expression.
        return self.expr

    def getIds(self):
        # Get the IDs of all objects for which the expression is True.
        return self.ids

    def getType(self):
        return self.meta_type

    def setExpression(self, expr):
        # Set the expression.
        self.expr = expr

    def __repr__(self):
        return '%s: (%s) %s' % (self.id,self.expr,map(None,self.ids))

    __str__ = __repr__


class PythonFilteredSet(FilteredSetBase):

    meta_type = 'PythonFilteredSet'

    def index_object(self, documentId, o):
        try:
            if RestrictionCapableEval(self.expr).eval({'o': o}):
                self.ids.insert(documentId)
            else:
                try:
                    self.ids.remove(documentId)
                except KeyError:
                    pass
        except ConflictError:
            raise
        except:
            LOG.warn('eval() failed Object: %s, expr: %s' %\
                     (o.getId(),self.expr), exc_info=sys.exc_info())


def factory(f_id, f_type, expr):
    """ factory function for FilteredSets """

    if f_type=='PythonFilteredSet':
        return PythonFilteredSet(f_id, expr)

    else:
        raise TypeError,'unknown type for FilteredSets: %s' % f_type
