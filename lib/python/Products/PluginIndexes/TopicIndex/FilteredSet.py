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

__version__ = '$Id: FilteredSet.py,v 1.4 2002/08/14 22:19:34 mj Exp $'

from BTrees.IIBTree import IISet
from Persistence import Persistent
from Globals import DTMLFile
from zLOG import WARNING,LOG
import sys


class FilteredSetBase(Persistent):

    def __init__(self, id, expr):
        self.id   = id
        self.expr = expr
        self.clear()


    def clear(self):
        self.ids  = IISet()


    def index_object(self, documentId, obj):
        raise RuntimeError,'index_object not defined'


    def unindex_object(self,documentId):
        try: self.ids.remove(Id)
        except: pass


    def getId(self):            return self.id
    def getExpression(self):    return self.expr
    def getIds(self):           return self.ids
    def getType(self):          return self.meta_type

    def setExpression(self, expr): self.expr = expr

    def __repr__(self):
        return '%s: (%s) %s' % (self.id,self.expr,map(None,self.ids))

    __str__ = __repr__



class PythonFilteredSet(FilteredSetBase):

    meta_type = 'PythonFilteredSet'

    def index_object(self, documentId, o):

        try:
            if eval(self.expr): self.ids.insert(documentId)
        except:
            LOG('FilteredSet',WARNING,'eval() failed',\
                'Object: %s, expr: %s' % (o.getId(),self.expr),\
                sys.exc_info())



def factory(f_id, f_type, expr):
    """ factory function for FilteredSets """

    if f_type=='PythonFilteredSet':
        return PythonFilteredSet(f_id, expr)

    else:
        raise TypeError,'unknown type for FilteredSets: %s' % f_type
