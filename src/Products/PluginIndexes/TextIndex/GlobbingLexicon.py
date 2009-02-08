##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
#############################################################################
import re
import string

from BTrees.IIBTree import IISet, union, IITreeSet
from BTrees.OIBTree import OIBTree
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree

from Products.PluginIndexes.common.randid import randid
from Products.PluginIndexes.TextIndex.TextIndex import Op
from Products.PluginIndexes.TextIndex.TextIndex import Or
from Products.PluginIndexes.TextIndex.Lexicon import Lexicon
from Products.PluginIndexes.TextIndex.Splitter import getSplitter

class GlobbingLexicon(Lexicon):
    """Lexicon which supports basic globbing function ('*' and '?').

    This lexicon keeps several data structures around that are useful
    for searching. They are:

      '_lexicon' -- Contains the mapping from word => word_id

      '_inverseLex' -- Contains the mapping from word_id => word

      '_digrams' -- Contains a mapping from digram => word_id

    Before going further, it is necessary to understand what a digram is,
    as it is a core component of the structure of this lexicon.  A digram
    is a two-letter sequence in a word.  For example, the word 'zope'
    would be converted into the digrams::

      ['$z', 'zo', 'op', 'pe', 'e$']

    where the '$' is a word marker.  It is used at the beginning and end
    of the words.  Those digrams are significant.
    """

    multi_wc = '*'
    single_wc = '?'
    eow = '$'


    def __init__(self,useSplitter=None,extra=None):
        self.clear()
        self.useSplitter = useSplitter
        self.splitterParams = extra
        self.SplitterFunc = getSplitter(self.useSplitter)

    def clear(self):
        self._lexicon = OIBTree()
        self._inverseLex = IOBTree()
        self._digrams = OOBTree()

    def _convertBTrees(self, threshold=200):
        Lexicon._convertBTrees(self, threshold)
        if type(self._digrams) is OOBTree: return

        from BTrees.convert import convert

        _digrams=self._digrams
        self._digrams=OOBTree()
        self._digrams._p_jar=self._p_jar
        convert(_digrams, self._digrams, threshold, IITreeSet)


    def createDigrams(self, word):
        """Returns a list with the set of digrams in the word."""

        word = '$'+word+'$'
        return [ word[i:i+2] for i in range(len(word)-1)]


    def getWordId(self, word):
        """Provided 'word', return the matching integer word id."""

        if self._lexicon.has_key(word):
            return self._lexicon[word]
        else:
            return self.assignWordId(word)

    set = getWordId                     # Kludge for old code

    def getWord(self, wid):
        return self._inverseLex.get(wid, None)

    def assignWordId(self, word):
        """Assigns a new word id to the provided word, and return it."""

        # Double check it's not in the lexicon already, and if it is, just
        # return it.
        if self._lexicon.has_key(word):
            return self._lexicon[word]


        # Get word id. BBB Backward compat pain.
        inverse=self._inverseLex
        try: insert=inverse.insert
        except AttributeError:
            # we have an "old" BTree object
            if inverse:
                wid=inverse.keys()[-1]+1
            else:
                self._inverseLex=IOBTree()
                wid=1
            inverse[wid] = word
        else:
            # we have a "new" IOBTree object
            wid=randid()
            while not inverse.insert(wid, word):
                wid=randid()

        self._lexicon[word] = wid

        # Now take all the digrams and insert them into the digram map.
        for digram in self.createDigrams(word):
            set = self._digrams.get(digram, None)
            if set is None:
                self._digrams[digram] = set = IISet()
            set.insert(wid)

        return wid


    def get(self, pattern):
        """ Query the lexicon for words matching a pattern."""

        # single word pattern  produce a slicing problem below.
        # Because the splitter throws away single characters we can
        # return an empty tuple here.

        if len(pattern)==1: return ()

        wc_set = [self.multi_wc, self.single_wc]

        digrams = []
        globbing = 0
        for i in range(len(pattern)):
            if pattern[i] in wc_set:
                globbing = 1
                continue

            if i == 0:
                digrams.insert(i, (self.eow + pattern[i]) )
                digrams.append((pattern[i] + pattern[i+1]))
            else:
                try:
                    if pattern[i+1] not in wc_set:
                        digrams.append( pattern[i] + pattern[i+1] )

                except IndexError:
                    digrams.append( (pattern[i] + self.eow) )

        if not globbing:
            result =  self._lexicon.get(pattern, None)
            if result is None:
                return ()
            return (result, )

        ## now get all of the intsets that contain the result digrams
        result = None
        for digram in digrams:
            result=union(result, self._digrams.get(digram, None))

        if not result:
            return ()
        else:
            ## now we have narrowed the list of possible candidates
            ## down to those words which contain digrams.  However,
            ## some words may have been returned that match digrams,
            ## but do not match 'pattern'.  This is because some words
            ## may contain all matching digrams, but in the wrong
            ## order.

            expr = re.compile(self.createRegex(pattern))
            words = []
            hits = IISet()
            for x in result:
                if expr.match(self._inverseLex[x]):
                    hits.insert(x)
            return hits


    def __getitem__(self, word):
        """ """
        return self.get(word)


    def query_hook(self, q):
        """expand wildcards"""
        ListType = type([])
        i = len(q) - 1
        while i >= 0:
            e = q[i]
            if isinstance(e, ListType):
                self.query_hook(e)
            elif isinstance(e, Op):
                pass
            elif ( (self.multi_wc in e) or
                   (self.single_wc in e) ):
                wids = self.get(e)
                words = []
                for wid in wids:
                    if words:
                        words.append(Or)
                    words.append(wid)
                if not words:
                    # if words is empty, return something that will make
                    # textindex's __getitem__ return an empty result list
                    words.append('')
                q[i] = words
            i = i - 1

        return q

    def Splitter(self, astring, words=None, encoding="latin1"):
        """ wrap the splitter """

        ## don't do anything, less efficient but there's not much
        ## sense in stemming a globbing lexicon.

        try:
            return self.SplitterFunc(
                    astring,
                    words,
                    encoding=encoding,
                    singlechar=self.splitterParams.splitterSingleChars,
                    indexnumbers=self.splitterParams.splitterIndexNumbers,
                    casefolding=self.splitterParams.splitterCasefolding
                    )
        except:
            return self.SplitterFunc(astring, words)


    def createRegex(self, pat):
        """Translate a PATTERN to a regular expression.

        There is no way to quote meta-characters.
        """

        # Remove characters that are meaningful in a regex
        if not isinstance(pat, unicode):
            transTable = string.maketrans("", "")
            result = string.translate(pat, transTable,
                                      r'()&|!@#$%^{}\<>.')
        else:
            transTable={}
            for ch in r'()&|!@#$%^{}\<>.':
                transTable[ord(ch)]=None
            result=pat.translate(transTable)

        # First, deal with multi-character globbing
        result = result.replace( '*', '.*')

        # Next, we need to deal with single-character globbing
        result = result.replace( '?', '.')

        return "%s$" % result
