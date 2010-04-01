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

"""Full text index with relevance ranking, using an Okapi BM25 rank."""

# Lots of comments are at the bottom of this file.  Read them to
# understand what's going on.

from BTrees.IIBTree import IIBucket
from BTrees.Length import Length
from zope.interface import implements

from Products.ZCTextIndex.IIndex import IIndex
from Products.ZCTextIndex.BaseIndex import BaseIndex
from Products.ZCTextIndex.BaseIndex import inverse_doc_frequency
from Products.ZCTextIndex.BaseIndex import scaled_int
from Products.ZCTextIndex.okascore import score

class OkapiIndex(BaseIndex):

    implements(IIndex)

    # BM25 free parameters.
    K1 = 1.2
    B  = 0.75
    assert K1 >= 0.0
    assert 0.0 <= B <= 1.0

    def __init__(self, lexicon):
        BaseIndex.__init__(self, lexicon)

        # ._wordinfo for Okapi is
        # wid -> {docid -> frequency}; t -> D -> f(D, t)

        # ._docweight for Okapi is
        # docid -> # of words in the doc
        # This is just len(self._docwords[docid]), but _docwords is stored
        # in compressed form, so uncompressing it just to count the list
        # length would be ridiculously expensive.

        # sum(self._docweight.values()), the total # of words in all docs
        # This is a long for "better safe than sorry" reasons.  It isn't
        # used often enough that speed should matter.
        # Use a BTree.Length.Length object to avoid concurrent write conflicts
        self._totaldoclen = Length(0L)

    def index_doc(self, docid, text):
        count = BaseIndex.index_doc(self, docid, text)
        self._change_doc_len(count)
        return count

    def _reindex_doc(self, docid, text):
        self._change_doc_len(-self._docweight[docid])
        return BaseIndex._reindex_doc(self, docid, text)

    def unindex_doc(self, docid):
        self._change_doc_len(-self._docweight[docid])
        BaseIndex.unindex_doc(self, docid)
    
    def _change_doc_len(self, delta):
        # Change total doc length used for scoring
        try:
            self._totaldoclen.change(delta)
        except AttributeError:
            # Opportunistically upgrade _totaldoclen attribute to Length object
            self._totaldoclen = Length(long(self._totaldoclen + delta))

    # The workhorse.  Return a list of (IIBucket, weight) pairs, one pair
    # for each wid t in wids.  The IIBucket, times the weight, maps D to
    # TF(D,t) * IDF(t) for every docid D containing t.
    # As currently written, the weights are always 1, and the IIBucket maps
    # D to TF(D,t)*IDF(t) directly, where the product is computed as a float
    # but stored as a scaled_int.
    # NOTE:  This is overridden below, by a function that computes the
    # same thing but with the inner scoring loop in C.
    def _search_wids(self, wids):
        if not wids:
            return []
        N = float(self.document_count())  # total # of docs
        try:
            doclen = self._totaldoclen()
        except TypeError:
            # _totaldoclen has not yet been upgraded
            doclen = self._totaldoclen
        meandoclen = doclen / N
        K1 = self.K1
        B = self.B
        K1_plus1 = K1 + 1.0
        B_from1 = 1.0 - B

        #                           f(D, t) * (k1 + 1)
        #   TF(D, t) =  -------------------------------------------
        #               f(D, t) + k1 * ((1-b) + b*len(D)/E(len(D)))

        L = []
        docid2len = self._docweight
        for t in wids:
            d2f = self._wordinfo[t] # map {docid -> f(docid, t)}
            idf = inverse_doc_frequency(len(d2f), N)  # an unscaled float
            result = IIBucket()
            for docid, f in d2f.items():
                lenweight = B_from1 + B * docid2len[docid] / meandoclen
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
        # of tf would still be done at Python speed, and it's a lot more
        # work than just multiplying by idf.

    # The same function as _search_wids above, but with the inner scoring
    # loop written in C (module okascore, function score()).
    # Cautions:  okascore hardcodes the values of K, B1, and the scaled_int
    # function.
    def _search_wids(self, wids):
        if not wids:
            return []
        N = float(self.document_count())  # total # of docs
        try:
            doclen = self._totaldoclen()
        except TypeError:
            # _totaldoclen has not yet been upgraded
            doclen = self._totaldoclen
        meandoclen = doclen / N
        #K1 = self.K1
        #B = self.B
        #K1_plus1 = K1 + 1.0
        #B_from1 = 1.0 - B

        #                           f(D, t) * (k1 + 1)
        #   TF(D, t) =  -------------------------------------------
        #               f(D, t) + k1 * ((1-b) + b*len(D)/E(len(D)))

        L = []
        docid2len = self._docweight
        for t in wids:
            d2f = self._wordinfo[t] # map {docid -> f(docid, t)}
            idf = inverse_doc_frequency(len(d2f), N)  # an unscaled float
            result = IIBucket()
            score(result, d2f.items(), docid2len, idf, meandoclen)
            L.append((result, 1))
        return L

    def query_weight(self, terms):
        # Get the wids.
        wids = []
        for term in terms:
            termwids = self._lexicon.termToWordIds(term)
            wids.extend(termwids)
        # The max score for term t is the maximum value of
        #     TF(D, t) * IDF(Q, t)
        # We can compute IDF directly, and as noted in the comments below
        # TF(D, t) is bounded above by 1+K1.
        N = float(len(self._docweight))
        tfmax = 1.0 + self.K1
        sum = 0
        for t in self._remove_oov_wids(wids):
            idf = inverse_doc_frequency(len(self._wordinfo[t]), N)
            sum += scaled_int(idf * tfmax)
        return sum

    def _get_frequencies(self, wids):
        d = {}
        dget = d.get
        for wid in wids:
            d[wid] = dget(wid, 0) + 1
        return d, len(wids)

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


Query Term Weighting
--------------------

I'm ignoring the query adjustment part of Okapi BM25 because I expect our
queries are very short.  Full BM25 takes them into account by adding the
following to every score(D, Q); it depends on the lengths of D and Q, but
not on the specific words in Q, or even on whether they appear in D(!):

                   E(len(D)) - len(D)
    k2 * len(Q) * -------------------
                   E(len(D)) + len(D)

Here k2 is another "tuning constant", len(Q) is the number of words in Q, and
len(D) & E(len(D)) were defined above. The Okapi group set k2 to 0 in TREC-9,
so it apparently doesn't do much good (or may even hurt).

Full BM25 *also* multiplies the following factor into IDF(Q, t):

    f(Q, t) * (k3 + 1)
    ------------------
       f(Q, t) + k3

where k3 is yet another free parameter, and f(Q,t) is the number of times t
appears in Q.  Since we're using short "web style" queries, I expect f(Q,t)
to always be 1, and then that quotient is

     1 * (k3 + 1)
     ------------ = 1
        1 + k3

regardless of k3's value.  So, in a trivial sense, we are incorporating
this measure (and optimizing it by not bothering to multiply by 1 <wink>).
"""
