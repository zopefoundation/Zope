##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Full text index with relevance ranking, using a cosine measure."""

import math

from BTrees.IOBTree import IOBTree
from BTrees.IIBTree import IIBTree, IIBucket

from Products.ZCTextIndex.IIndex import IIndex
from Products.ZCTextIndex import WidCode
from Products.ZCTextIndex.BaseIndex import BaseIndex, inverse_doc_frequency
from Products.ZCTextIndex.SetOps import mass_weightedIntersection, \
                                        mass_weightedUnion

import ZODB

# Instead of storing floats, we generally store scaled ints.  Binary pickles
# can store those more efficiently.  The default SCALE_FACTOR of 1024
# is large enough to get about 3 decimal digits of fractional info, and
# small enough so that scaled values should almost always fit in a signed
# 16-bit int (we're generally storing logs, so a few bits before the radix
# point goes a long way; on the flip side, for reasonably small numbers x
# most of the info in log(x) is in the fractional bits, so we do want to
# save a lot of those).
SCALE_FACTOR = 1024.0

def scaled_int(f, scale=SCALE_FACTOR):
    # We expect only positive inputs, so "add a half and chop" is the
    # same as round().  Surprising, calling round() is significantly more
    # expensive.
    return int(f * scale + 0.5)

class CosineIndex(BaseIndex):

    __implements__ = IIndex

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

    def index_doc(self, docid, text):
        wids = self._lexicon.sourceToWordIds(text)
        uniqwids, freqs, docweight = self._get_frequencies(wids)
        for i in range(len(uniqwids)):
            self._add_wordinfo(uniqwids[i], freqs[i], docid)
        self._docweight[docid] = docweight
        self._add_undoinfo(docid, wids)
        return len(wids)

    def unindex_doc(self, docid):
        for wid in self.get_words(docid):
            self._del_wordinfo(wid, docid)
        del self._docwords[docid]
        del self._docweight[docid]

    def _search_wids(self, wids):
        if not wids:
            return []
        N = float(len(self._docweight))
        L = []
        DictType = type({})
        for wid in wids:
            assert self._wordinfo.has_key(wid)  # caller responsible for OOV
            d2w = self._wordinfo[wid] # maps docid to w(docid, wid)
            idf = inverse_doc_frequency(len(d2w), N)  # this is an unscaled float
            #print "idf = %.3f" % idf
            if isinstance(d2w, DictType):
                d2w = IIBucket(d2w)
            L.append((d2w, scaled_int(idf)))
        return L

    def query_weight(self, terms):
        wids = []
        for term in terms:
            wids += self._lexicon.termToWordIds(term)
        N = float(len(self._docweight))
        sum = 0.0
        for wid in wids:
            if wid == 0:
                continue
            map = self._wordinfo.get(wid)
            if map is None:
                continue
            wt = math.log(1.0 + N / len(map))
            sum += wt ** 2.0
        return scaled_int(math.sqrt(sum))

    def _get_frequencies(self, wids):
        """Return individual doc-term weights and docweight."""
        # Computes w(d, t) for each term, and W(d).
        # Return triple:
        #    [wid0, wid1, ...],
        #    [w(d, wid0)/W(d), w(d, wid1)/W(d), ...],
        #    W(d)
        # The second list and W(d) are scaled_ints.
        d = {}
        for wid in wids:
            d[wid] = d.get(wid, 0) + 1
        Wsquares = 0.0
        weights = []
        push = weights.append
        for count in d.values():
            w = doc_term_weight(count)
            Wsquares += w * w
            push(w)
        W = math.sqrt(Wsquares)
        #print "W = %.3f" % W
        for i in xrange(len(weights)):
            #print i, ":", "%.3f" % weights[i],
            weights[i] = scaled_int(weights[i] / W)
            #print "->", weights[i]
        return d.keys(), weights, scaled_int(W)

    DICT_CUTOFF = 10

    def _add_wordinfo(self, wid, f, docid):
        # Store a wordinfo in a dict as long as there are less than
        # DICT_CUTOFF docids in the dict.  Otherwise use an IIBTree.

        # The pickle of a dict is smaller than the pickle of an
        # IIBTree, substantially so for small mappings.  Thus, we use
        # a dictionary until the mapping reaches DICT_CUTOFF elements.

        # The cutoff is chosen based on the implementation
        # characteristics of Python dictionaries.  The dict hashtable
        # always has 2**N slots and is resized whenever it is 2/3s
        # full.  A pickled dict with 10 elts is half the size of an
        # IIBTree with 10 elts, and 10 happens to be 2/3s of 2**4.  So
        # choose 10 as the cutoff for now.

        # The IIBTree has a smaller in-memory representation than a
        # dictionary, so pickle size isn't the only consideration when
        # choosing the threshold.  The pickle of a 500-elt dict is 92%
        # of the size of the same IIBTree, but the dict uses more
        # space when it is live in memory.  An IIBTree stores two C
        # arrays of ints, one for the keys and one for the values.  It
        # holds upto 120 key-value pairs in a single bucket.
        try:
            map = self._wordinfo[wid]
        except KeyError:
            map = {}
        else:
            # _add_wordinfo() is called for each update.  If the map
            # size exceeds the DICT_CUTOFF, convert to an IIBTree.
            if len(map) == self.DICT_CUTOFF:
                map = IIBTree(map)
        map[docid] = f
        self._wordinfo[wid] = map # Not redundant, because of Persistency!

    def _del_wordinfo(self, wid, docid):
        try:
            map = self._wordinfo[wid]
            del map[docid]
        except KeyError:
            return
        if len(map) == 0:
            del self._wordinfo[wid]
            return
        if len(map) == self.DICT_CUTOFF:
            new = {}
            for k, v in map.items():
                new[k] = v
            map = new
        self._wordinfo[wid] = map # Not redundant, because of Persistency!

    def _add_undoinfo(self, docid, wids):
        self._docwords[docid] = WidCode.encode(wids)

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
