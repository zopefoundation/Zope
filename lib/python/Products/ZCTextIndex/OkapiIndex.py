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

"""Full text index with relevance ranking, using an Okapi BM25 rank."""

# Lots of comments are at the bottom of this file.  Read them to
# understand what's going on.

import math

from BTrees.IOBTree import IOBTree
from BTrees.IIBTree import IIBTree, IIBucket

from Products.ZCTextIndex.IIndex import IIndex
from Products.ZCTextIndex.NBest import NBest
from Products.ZCTextIndex import WidCode
from Products.ZCTextIndex.SetOps import mass_weightedIntersection, \
                                        mass_weightedUnion

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

class Index:

    __implements__ = IIndex

    # BM25 free parameters.
    K1 = 1.2
    B  = 0.75
    assert K1 >= 0.0
    assert 0.0 <= B <= 1.0

    def __init__(self, lexicon):
        self._lexicon = lexicon

        # wid -> { docid -> frequency }; t -> D -> f(D, t)
        self._wordinfo = IOBTree()

        # docid -> # of words in the doc
        # XXX this is just len(self._docwords[docid]), but if _docwords
        # XXX is stored in compressed form then uncompressing just to count
        # XXX the list length would be ridiculously expensive.
        self._doclen = IIBTree()

        # docid -> [ wid ]
        # used for un-indexing
        self._docwords = IOBTree()

        # sum(self._doclen.values()), the total # of words in all docs
        self._totaldoclen = 0L

    def length(self):
        """Return the number of documents in the index."""
        return len(self._docwords)

    # Most of the computation for computing a relevance score for the
    # document occurs in the search() method.

    def index_doc(self, docid, text):
        wids = self._lexicon.sourceToWordIds(text)
        self._doclen[docid] = len(wids)
        self._totaldoclen += len(wids)
        wid2count = self._get_frequencies(wids)
        for wid, count in wid2count.items():
            self._add_wordinfo(wid, count, docid)
        self._add_undoinfo(docid, wids)

    def unindex_doc(self, docid):
        for wid in self._get_undoinfo(docid):
            self._del_wordinfo(wid, docid)
        del self._docwords[docid]
        count = self._doclen[docid]
        del self._doclen[docid]
        self._totaldoclen -= count

    def search(self, term):
        wids = self._lexicon.termToWordIds(term)
        return mass_weightedUnion(self._search_wids(wids))

    def search_glob(self, pattern):
        wids = self._lexicon.globToWordIds(pattern)
        return mass_weightedUnion(self._search_wids(wids))

    def search_phrase(self, phrase):
        wids = self._lexicon.termToWordIds(phrase)
        hits = mass_weightedIntersection(self._search_wids(wids))
        if not hits:
            return hits
        code = WidCode.encode(wids)
        result = IIBTree()
        for docid, weight in hits.items():
            docwords = self._docwords[docid]
            if docwords.find(code) >= 0:
                result[docid] = weight
        return result

    def _search_wids(self, wids):
        if not wids:
            return []
        N = float(len(self._doclen))
        L = []
        K1 = self.K1
        B = self.B
        K1_plus1 = K1 + 1.0
        B_from1 = 1.0 - B
        meandoclen = self._totaldoclen / N

        #                           f(D, t) * (k1 + 1)
        #   TF(D, t) =  -------------------------------------------
        #               f(D, t) + k1 * ((1-b) + b*len(D)/E(len(D)))

        for wid in wids:
            d2f = self._wordinfo[wid] # map {docid -> f(docid, wid)}
            idf = inverse_doc_frequency(len(d2f), N)  # this is an unscaled float
            result = IIBucket()
            for docid, f in d2f.items():
                lenweight = B_from1 + B * self._doclen[docid] / meandoclen
                tf = f * K1_plus1 / (f + K1 * lenweight)
                result[docid] = scaled_int(tf * idf)
            L.append((result, 1))
        return L

        # Note about the above:  the result is tf * idf.  tf is small -- it
        # can't be larger than k1+1 = 2.2.  idf is formally unbounded, but
        # is less than 14 for a term that appears in only 1 of a million
        # documents.  So the product is probably less than 32, or 5 bits
        # before the radix point.  If we did the scaled-int business on
        # both of them, we'd be up to 25 bits.  Add 64 of those and we'd
        # be in overflow territory.  That's pretty unlikely, so we *could*
        # just store scaled_int(tf) in result[docid], and use scaled_int(idf)
        # as an invariant weight across the whole result.  But besides
        # skating near the edge, it's not a speed cure, since the computation
        # of tf would still done at Python speed, and it's a lot more
        # work than just multiplying by idf.

    def query_weight(self, terms):
        # XXX I have no idea what to put here
        return 10

    def _get_frequencies(self, wids):
        """Return individual term frequencies."""
        # Computes f(d, t) for each term.
        # Returns a dict mapping wid to the number of times wid appeared
        # in wids, {t: f(d, t)}
        d = {}
        dget = d.get
        for wid in wids:
            d[wid] = dget(wid, 0) + 1
        return d

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

    def _get_undoinfo(self, docid):
        return WidCode.decode(self._docwords[docid])

    # The rest are helper methods to support unit tests
    # XXX These don't work for Okapi, I assume

    def _get_wdt(self, d, t):
        wid, = self._lexicon.termToWordIds(t)
        map = self._wordinfo[wid]
        return map.get(d, 0) * self._doclen[d] / SCALE_FACTOR

    def _get_Wd(self, d):
        return self._doclen[d]

    def _get_ft(self, t):
        wid, = self._lexicon.termToWordIds(t)
        return len(self._wordinfo[wid])

    def _get_wt(self, t):
        wid, = self._lexicon.termToWordIds(t)
        map = self._wordinfo[wid]
        return scaled_int(math.log(1 + len(self._docweight) / float(len(map))))

def inverse_doc_frequency(term_count, num_items):
    """Return the inverse doc frequency for a term,

    that appears in term_count items in a collection with num_items
    total items.
    """
    # implements IDF(q, t) = log(1 + N/f(t))
    return math.log(1.0 + float(num_items) / term_count)

"""
"Okapi" (much like "cosine rule" also) is a large family of scoring gimmicks.
It's based on probability arguments about how words are distributed in
documents, not on an abstract vector space model.  A long paper by its
principal inventors gives an excellent overview of how it was derived:

    A probabilistic model of information retrieval:  development and status
    K. Sparck Jones, S. Walker, S.E. Robertson
    http://citeseer.nj.nec.com/jones98probabilistic.html

Spellings that ignore relevance information (which we don't have) are of this
high-level form:

    score(D, Q) = sum(for t in D&Q: TF(D, t) * IDF(Q, t))

where

    D         a specific document

    Q         a specific query

    t         a term (word, atomic phrase, whatever)

    D&Q       the terms common to D and Q

    TF(D, t)  a measure of t's importance in D -- a kind of term frequency
              weight

    IDF(Q, t) a measure of t's importance in the query and in the set of
              documents as a whole -- a kind of inverse document frequency
              weight

The IDF(Q, t) here is identical to the one used for our cosine measure.
Since queries are expected to be short, it ignores Q entirely:

   IDF(Q, t) = log(1.0 + N / f(t))

where

   N        the total number of documents
   f(t)     the number of documents in which t appears

Most Okapi literature seems to use log(N/f(t)) instead.  We don't, because
that becomes 0 for a term that's in every document, and, e.g., if someone
is searching for "documentation" on python.org (a term that may well show
up on every page, due to the top navigation bar), we still want to find the
pages that use the word a lot (which is TF's job to find, not IDF's -- we
just want to stop IDF from considering this t to be irrelevant).

The TF(D, t) spellings are more interesting.  With lots of variations, the
most basic spelling is of the form

                   f(D, t)
    TF(D, t) = ---------------
                f(D, t) + K(D)

where

    f(D, t)   the number of times t appears in D
    K(D)      a measure of the length of D, normalized to mean doc length

The functional *form* f/(f+K) is clever.  It's a gross approximation to a
mixture of two distinct Poisson distributions, based on the idea that t
probably appears in D for one of two reasons:

1. More or less at random.

2. Because it's important to D's purpose in life ("eliteness" in papers).

Note that f/(f+K) is always between 0 and 1.  If f is very large compared to
K, it approaches 1.  If K is very large compared to f, it approaches 0.  If
t appears in D more or less "for random reasons", f is likely to be small,
and so K will dominate unless it's a very small doc, and the ratio will be
small.  OTOH, if t appears a lot in D, f will dominate unless it's a very
large doc, and the ratio will be close to 1.

We use a variation on that simple theme, a simplification of what's called
BM25 in the literature (it was the 25th stab at a Best Match function from
the Okapi group; "a simplification" means we're setting some of BM25's more
esoteric free parameters to 0):

                f(D, t) * (k1 + 1)
    TF(D, t) = --------------------
                f(D, t) + k1 * K(D)

where

    k1      a "tuning factor", typically between 1.0 and 2.0.  We use 1.2,
            the usual default value.  This constant adjusts the curve to
            look more like a theoretical 2-Poisson curve.

Note that as f(D, t) increases, TF(D, t) increases monotonically, approaching
an asymptote of k1+1 from below.

Finally, we use

    K(D) = (1-b) + b * len(D)/E(len(D))

where

    b           is another free parameter, discussed below.  We use 0.75.

    len(D)      the length of D in words

    E(len(D))   the expected value of len(D) across the whole document set;
                or, IOW, the average document length

b is a free parameter between 0.0 and 1.0, and adjusts for the expected effect
of the "Verbosity Hypothesis".  Suppose b is 1, and some word t appears
10 times as often in document d2 than in document d1.  If document d2 is
also 10 times as long as d1, TF(d1, t) and TF(d2, t) are identical:

                     f(d2, t) * (k1 + 1)
   TF(d2, t) = --------------------------------- =
                f(d2, t) + k1 * len(d2)/E(len(D))

                            10 * f(d1, t) * (k1 + 1)
               ----------------------------------------------- = TF(d1, t)
                10 * f(d1, t) + k1 * (10 * len(d1))/E(len(D))

because the 10's cancel out.  This is appropriate if we believe that a word
appearing 10x more often in a doc 10x as long is simply due to that the
longer doc is more verbose.  If we do believe that, the longer doc and the
shorter doc are probably equally relevant.  OTOH, it *could* be that the
longer doc is talking about t in greater depth too, in which case it's
probably more relevant than the shorter doc.

At the other extreme, if we set b to 0, the len(D)/E(len(D)) term vanishes
completely, and a doc scores higher for having more occurences of a word
regardless of the doc's length.

Reality is between these extremes, and probably varies by document and word
too.  Reports in the literature suggest that b=0.75 is a good compromise "in
general", favoring the "verbosity hypothesis" end of the scale.

Putting it all together, the final TF function is

                           f(D, t) * (k1 + 1)
    TF(D, t) = --------------------------------------------
                f(D, t) + k1 * ((1-b) + b*len(D)/E(len(D)))

with k1=1.2 and b=0.75.
"""
