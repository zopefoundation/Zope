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
        self.__wids = OIBTree()
        self.__words = IOBTree()
        # XXX we're reserving wid 0, but that might be yagni
        self.__nextwid = 1
        self.__pipeline = pipeline

    def length(self):
        """Return the number of unique terms in the lexicon."""
        return self.__nextwid - 1

    def words(self):
        return self.__wids.keys()

    def wids(self):
        return self.__words.keys()

    def items(self):
        return self.__wids.items()

    def sourceToWordIds(self, text):
        last = _text2list(text)
        for element in self.__pipeline:
            last = element.process(last)
        return map(self._getWordIdCreate, last)

    def termToWordIds(self, text):
        last = _text2list(text)
        for element in self.__pipeline:
            last = element.process(last)
        wids = []
        for word in last:
            wid = self.__wids.get(word)
            if wid is not None:
                wids.append(wid)
        return wids

    def globToWordIds(self, pattern):
        if not re.match("^\w+\*$", pattern):
            return []
        pattern = pattern.lower()
        assert pattern.endswith("*")
        prefix = pattern[:-1]
        assert prefix and not prefix.endswith("*")
        keys = self.__wids.keys(prefix) # Keys starting at prefix
        wids = []
        words = []
        for key in keys:
            if not key.startswith(prefix):
                break
            wids.append(self.__wids[key])
            words.append(key)
        return wids

    def _getWordIdCreate(self, word):
        wid = self.__wids.get(word)
        if wid is None:
            wid = self.__new_wid()
            self.__wids[word] = wid
            self.__words[wid] = word
        return wid

    def __new_wid(self):
        wid = self.__nextwid
        self.__nextwid += 1
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

    def process(self, lst):
        result = []
        for s in lst:
            result += self.rx.findall(s)
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
