##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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

import re

from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from Products.ZCTextIndex.ILexicon import ILexicon
from Products.ZCTextIndex.StopDict import get_stopdict

class Lexicon:

    __implements__ = ILexicon

    def __init__(self, *pipeline):
        self._wids = OIBTree()  # word -> wid
        self._words = IOBTree() # wid -> word
        # wid 0 is reserved for words that aren't in the lexicon (OOV -- out
        # of vocabulary).  This can happen, e.g., if a query contains a word
        # we never saw before, and that isn't a known stopword (or otherwise
        # filtered out).  Returning a special wid value for OOV words is a
        # way to let clients know when an OOV word appears.
        self._nextwid = 1
        self._pipeline = pipeline

        # Keep some statistics about indexing
        self._nbytes = 0 # Number of bytes indexed (at start of pipeline)
        self._nwords = 0 # Number of words indexed (after pipeline)

    def length(self):
        """Return the number of unique terms in the lexicon."""
        return self._nextwid - 1

    def words(self):
        return self._wids.keys()

    def wids(self):
        return self._words.keys()

    def items(self):
        return self._wids.items()

    def sourceToWordIds(self, text):
        last = _text2list(text)
        for t in last:
            self._nbytes += len(t)
        for element in self._pipeline:
            last = element.process(last)
        self._nwords += len(last)
        return map(self._getWordIdCreate, last)

    def termToWordIds(self, text):
        last = _text2list(text)
        for element in self._pipeline:
            last = element.process(last)
        wids = []
        for word in last:
            wids.append(self._wids.get(word, 0))
        return wids

    def parseTerms(self, text):
        last = _text2list(text)
        for element in self._pipeline:
            process = getattr(element, "processGlob", element.process)
            last = process(last)
        return last

    def isGlob(self, word):
        return "*" in word

    def get_word(self, wid):
        return self._words[wid]

    def get_wid(self, word):
        return self._wids.get(word, 0)

    def globToWordIds(self, pattern):
        if not re.match("^\w+\*$", pattern):
            return []
        pattern = pattern.lower()
        assert pattern.endswith("*")
        prefix = pattern[:-1]
        assert prefix and not prefix.endswith("*")
        keys = self._wids.keys(prefix) # Keys starting at prefix
        wids = []
        for key in keys:
            if not key.startswith(prefix):
                break
            wids.append(self._wids[key])
        return wids

    def _getWordIdCreate(self, word):
        wid = self._wids.get(word)
        if wid is None:
            wid = self._new_wid()
            self._wids[word] = wid
            self._words[wid] = word
        return wid

    def _new_wid(self):
        wid = self._nextwid
        self._nextwid += 1
        return wid

def _text2list(text):
    # Helper: splitter input may be a string or a list of strings
    try:
        text + ""
    except:
        return text
    else:
        return [text]

# Sample pipeline elements

class Splitter:

    import re
    rx = re.compile(r"\w+")
    rxGlob = re.compile(r"\w+\*?")

    def process(self, lst):
        result = []
        for s in lst:
            result += self.rx.findall(s)
        return result

    def processGlob(self, lst):
        result = []
        for s in lst:
            result += self.rxGlob.findall(s)
        return result

class CaseNormalizer:

    def process(self, lst):
        return [w.lower() for w in lst]

class StopWordRemover:

    dict = get_stopdict().copy()
    for c in range(255):
        dict[chr(c)] = None

    def process(self, lst):
        has_key = self.dict.has_key
        return [w for w in lst if not has_key(w)]

try:
    from Products.ZCTextIndex import stopper as _stopper
except ImportError:
    pass
else:
    _stopwords = StopWordRemover.dict
    def StopWordRemover():
        swr = _stopper.new()
        swr.dict.update(_stopwords)
        return swr
