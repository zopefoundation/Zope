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

"""Abstract base class for full text index with relevance ranking."""


import math

from BTrees.IOBTree import IOBTree
from BTrees.IIBTree import IIBTree, IIBucket

from Products.ZCTextIndex.IIndex import IIndex
from Products.ZCTextIndex import WidCode
from Products.ZCTextIndex.SetOps import mass_weightedIntersection, \
                                        mass_weightedUnion

import ZODB
from Persistence import Persistent

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

class BaseIndex(Persistent):

    __implements__ = IIndex

    def __init__(self, lexicon):
        self._lexicon = lexicon

        # wid -> {docid -> weight}; t -> D -> w(D, t)
        # Different indexers have different notions of term weight, but we
        # expect each indexer to use ._wordinfo to map wids to its notion
        # of a docid-to-weight map.
        # There are two kinds of OOV words:  wid 0 is explicitly OOV,
        # and it's possible that the lexicon will return a non-zero wid
        # for a word *we've* never seen (e.g., lexicons can be shared
        # across indices, and a query can contain a word some other
        # index knows about but we don't).  A word is in-vocabulary for
        # this index if and only if _wordinfo.has_key(wid).  Note that
        # wid 0 must not be a key in _wordinfo.
        self._wordinfo = IOBTree()

        # docid -> weight
        # Different indexers have different notions of doc weight, but we
        # expect each indexer to use ._docweight to map docids to its
        # notion of what a doc weight is.
        self._docweight = IIBTree()

        # docid -> WidCode'd list of wids
        # Used for un-indexing, and for phrase search.
        self._docwords = IOBTree()

    def length(self):
        """Return the number of documents in the index."""
        return len(self._docwords)

    def get_words(self, docid):
        """Returns the wordids for a given docid"""
        return WidCode.decode(self._docwords[docid])

    # Subclass must override.
    def index_doc(self, docid, text):
        raise NotImplementedError

    # Subclass must override.
    def unindex_doc(self, docid):
        raise NotImplementedError

    def search(self, term):
        wids = self._lexicon.termToWordIds(term)
        if not wids:
            return None # All docs match
        wids = self._remove_oov_wids(wids)
        return mass_weightedUnion(self._search_wids(wids))

    def search_glob(self, pattern):
        wids = self._lexicon.globToWordIds(pattern)
        return mass_weightedUnion(self._search_wids(wids))

    def search_phrase(self, phrase):
        wids = self._lexicon.termToWordIds(phrase)
        cleaned_wids = self._remove_oov_wids(wids)
        if len(wids) != len(cleaned_wids):
            # At least one wid was OOV:  can't possibly find it.
            return IIBTree()
        scores = self._search_wids(cleaned_wids)
        hits = mass_weightedIntersection(scores)
        if not hits:
            return hits
        code = WidCode.encode(wids)
        result = IIBTree()
        for docid, weight in hits.items():
            docwords = self._docwords[docid]
            if docwords.find(code) >= 0:
                result[docid] = weight
        return result

    def _remove_oov_wids(self, wids):
        return filter(self._wordinfo.has_key, wids)

    # Subclass must override.
    # The workhorse.  Return a list of (IIBucket, weight) pairs, one pair
    # for each wid t in wids.  The IIBucket, times the weight, maps D to
    # TF(D,t) * IDF(t) for every docid D containing t.  wids must not
    # contain any OOV words.
    def _search_wids(self, wids):
        raise NotImplementedError

    def query_weight(self, terms):
        # This method was inherited from the cosine measure, and doesn't
        # make sense for Okapi measures in the way the cosine measure uses
        # it.  See the long comment at the end of the file for how full
        # Okapi BM25 deals with weighting query terms.
        return 10   # arbitrary

    def _get_frequencies(self, wids):
        """Return individual term frequencies."""
        # Computes f(d, t) for each term.
        # Returns a dict mapping wid to the number of times wid appeares
        # in wids, {t -> f(d, t)}
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

def inverse_doc_frequency(term_count, num_items):
    """Return the inverse doc frequency for a term,

    that appears in term_count items in a collection with num_items
    total items.
    """
    # implements IDF(q, t) = log(1 + N/f(t))
    return math.log(1.0 + float(num_items) / term_count)
