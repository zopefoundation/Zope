#############################################################################
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

from BTrees.IIBTree import IIBucket,IISet
from BTrees.OOBTree import OOSet
from BTrees.IIBTree import weightedIntersection,  difference
from BTrees.IIBTree import union as Iunion
from BTrees.IIBTree import intersection as Iintersection
from BTrees.OOBTree import union as Ounion

from types import TupleType
from TextIndexCommon import debug


class ResultListNG:
    """ class to keep results for TextIndexNG queries """
  
    def __init__(self, d, words, index):

        # usually instance of TextIndexNG
        self._index = index

        # words is either an OOSet or a mapping
        if type(words) is not OOSet: words=OOSet(words)
        self._words = words

        self._dict = d        

        self.keys    = self._dict.keys
        self.values  = self._dict.values
        self.items   = self._dict.items


    def Intersection(self,d1,d2):   
        """ Intersection between the documentIds (keys) of two dictionaries.
            The list of positions are merged.
        """

        r = {}

        docIds = Iintersection(
                    IISet(d1.keys()),
                    IISet(d2.keys())
                    )
            
        for docId in docIds: 
            r[docId] = Iunion( d1[docId], d2[docId])

        return r


    def Union(self,d1,d2):
        """ Union of the documentIds (keys) of two dictionaries.
            The list of positions are merged.
        """

        r = d1.copy()
            
        for docId in d2.keys():

            if d1.has_key(docId):
                r[docId] = Iunion( d1[docId], d2[docId])
            else:
                r[docId] = d2[docId]

        return r
            
            

    def __and__(self, x):
        """ and """

        return self.__class__(
            self.Intersection(self._dict, x._dict),
            Ounion(self._words, x._words),
            self._index,
            )


    def and_not(self, x):
        """ and not  """

        return self.__class__(
            difference(self._dict, x._dict),
            self._words,
            self._index,
            )
  
    def __or__(self, x):
        """ or """

        return self.__class__(
            self.Union(self._dict, x._dict),
            Ounion(self._words, x._words),
            self._index,
            )


    def near(self, x):
        """ near search """

        debug('-'*78)
        debug('entering near:')
        debug(self._words)
        debug(x._words)


        result = IIBucket()

        dict  = self._dict
        xdict = x._dict

        positions = self._index.positions

        debug("applying near search for documents:")
        debug("\t",dict)
        debug("\t",xdict)

        # inters is an IISet() with documentIds.
        
        inters = self.Intersection(dict, xdict)

        debug("Intersection is:")
        debug('\t',inters)

        for docId in inters.keys():

            debug('searching for positions',docId,self._words)
            p1 = positions(docId, self._words)
           
            debug('searching for positions',docId,x._words)
            p2 = positions(docId, x._words)

            leftPositions = IISet() 
            for set in p1.values():
                leftPositions = Iunion(leftPositions,set)

            rightPositions = IISet() 
            for set in p2.values():
                rightPositions = Iunion(rightPositions,set)


            for pl in leftPositions:
                for pr in rightPositions:
                    diff = abs(pl - pr)
                
                    if diff < 4:
                        debug('difference for (%d,%d): %d' % (pl,pr,diff))
                        result[docId] = 0


        return self.__class__(
            result, Ounion(self._words, x._words), self._index)
