##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Full text index with relevance ranking, using a cosine measure."""

import math

from BTrees.IIBTree import IIBucket
from zope.interface import implements

from Products.ZCTextIndex.IIndex import IIndex
from Products.ZCTextIndex.BaseIndex import BaseIndex
from Products.ZCTextIndex.BaseIndex import inverse_doc_frequency
from Products.ZCTextIndex.BaseIndex import scaled_int
from Products.ZCTextIndex.BaseIndex import SCALE_FACTOR

class CosineIndex(BaseIndex):

    implements(IIndex)

    def __init__(self, lexicon):
        BaseIndex.__init__(self, lexicon)

        # ._wordinfo for cosine is wid -> {docid -> weight};
        # t -> D -> w(d, t)/W(d)

        # ._docweight for cosine is
        # docid -> W(docid)

    # Most of the computation for computing a relevance score for the
    # document occurs in the _search_wids() method.  The code currently
    # implements the cosine similarity function described in Managing
    # Gigabytes, eq. 4.3, p. 187.  The index_object() method
    # precomputes some values that are independent of the particular
    # query.

    # The equation is
    #
    #                     sum(for t in I(d,q): w(d,t) * w(q,t))
    #     cosine(d, q) =  -------------------------------------
    #                                  W(d) * W(q)
    #
    # where
    #    I(d, q) = the intersection of the terms in d and q.
    #
    #    w(d, t) = 1 + log f(d, t)
    #        computed by doc_term_weight(); for a given word t,
    #        self._wordinfo[t] is a map from d to w(d, t).
    #
    #    w(q, t) = log(1 + N/f(t))
    #        computed by inverse_doc_frequency()
    #
    #    W(d) = sqrt(sum(for t in d: w(d, t) ** 2))
    #        computed by _get_frequencies(), and remembered in
    #        self._docweight[d]
    #
    #    W(q) = sqrt(sum(for t in q: w(q, t) ** 2))
    #        computed by self.query_weight()

    def _search_wids(self, wids):
        if not wids:
            return []
        N = float(self.document_count())
        L = []
        DictType = type({})
        for wid in wids:
            assert self._wordinfo.has_key(wid)  # caller responsible for OOV
            d2w = self._wordinfo[wid] # maps docid to w(docid, wid)
            idf = inverse_doc_frequency(len(d2w), N)  # an unscaled float
            #print "idf = %.3f" % idf
            if isinstance(d2w, DictType):
                d2w = IIBucket(d2w)
            L.append((d2w, scaled_int(idf)))
        return L

    def query_weight(self, terms):
        wids = []
        for term in terms:
            wids += self._lexicon.termToWordIds(term)
        N = float(self.document_count())
        sum = 0.0
        for wid in self._remove_oov_wids(wids):
            wt = inverse_doc_frequency(len(self._wordinfo[wid]), N)
            sum += wt ** 2.0
        return scaled_int(math.sqrt(sum))

    def _get_frequencies(self, wids):
        d = {}
        dget = d.get
        for wid in wids:
            d[wid] = dget(wid, 0) + 1
        Wsquares = 0.0
        for wid, count in d.items():
            w = doc_term_weight(count)
            Wsquares += w * w
            d[wid] = w
        W = math.sqrt(Wsquares)
        #print "W = %.3f" % W
        for wid, weight in d.items():
            #print i, ":", "%.3f" % weight,
            d[wid] = scaled_int(weight / W)
            #print "->", d[wid]
        return d, scaled_int(W)

    # The rest are helper methods to support unit tests

    def _get_wdt(self, d, t):
        wid, = self._lexicon.termToWordIds(t)
        map = self._wordinfo[wid]
        return map.get(d, 0) * self._docweight[d] / SCALE_FACTOR

    def _get_Wd(self, d):
        return self._docweight[d]

    def _get_ft(self, t):
        wid, = self._lexicon.termToWordIds(t)
        return len(self._wordinfo[wid])

    def _get_wt(self, t):
        wid, = self._lexicon.termToWordIds(t)
        map = self._wordinfo[wid]
        return scaled_int(math.log(1 + len(self._docweight) / float(len(map))))

def doc_term_weight(count):
    """Return the doc-term weight for a term that appears count times."""
    # implements w(d, t) = 1 + log f(d, t)
    return 1.0 + math.log(count)
