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

__doc__=""" Module breaks out Zope specific methods and behavior.  In
addition, provides the Lexicon class which defines a word to integer
mapping.

"""

import Splitter
from Persistence import Persistent
from Acquisition import Implicit

from BTrees.OIBTree import OIBTree
from BTrees.IOBTree import IOBTree
from BTrees.IIBTree import IISet, IITreeSet
from Products.PluginIndexes.common.randid import randid

from types import StringType

class Lexicon(Persistent, Implicit):
    """Maps words to word ids and then some

    The Lexicon object is an attempt to abstract vocabularies out of
    Text indexes.  This abstraction is not totally cooked yet, this
    module still includes the parser for the 'Text Index Query
    Language' and a few other hacks.

    """

    # default for older objects
    stop_syn={}

    def __init__(self, stop_syn=None,useSplitter=None,extra=None):

        self.clear()
        if stop_syn is None:
            self.stop_syn = {}
        else:
            self.stop_syn = stop_syn

        self.useSplitter = Splitter.splitterNames[0]
        if useSplitter: self.useSplitter=useSplitter
        self.splitterParams = extra
        self.SplitterFunc = Splitter.getSplitter(self.useSplitter)


    def clear(self):
        self._lexicon = OIBTree()
        self._inverseLex = IOBTree()

    def _convertBTrees(self, threshold=200):
        if (type(self._lexicon) is OIBTree and
            type(getattr(self, '_inverseLex', None)) is IOBTree):
            return

        from BTrees.convert import convert

        lexicon=self._lexicon
        self._lexicon=OIBTree()
        self._lexicon._p_jar=self._p_jar
        convert(lexicon, self._lexicon, threshold)

        try:
            inverseLex=self._inverseLex
            self._inverseLex=IOBTree()
        except AttributeError:
            # older lexicons didn't have an inverse lexicon
            self._inverseLex=IOBTree()
            inverseLex=self._inverseLex

        self._inverseLex._p_jar=self._p_jar
        convert(inverseLex, self._inverseLex, threshold)

    def set_stop_syn(self, stop_syn):
        """ pass in a mapping of stopwords and synonyms.  Format is:

        {'word' : [syn1, syn2, ..., synx]}

        Vocabularies do not necesarily need to implement this if their
        splitters do not support stemming or stoping.

        """
        self.stop_syn = stop_syn


    def getWordId(self, word):
        """ return the word id of 'word' """

        wid=self._lexicon.get(word, None)
        if wid is None:
            wid=self.assignWordId(word)
        return wid

    set = getWordId

    def getWord(self, wid):
        """ post-2.3.1b2 method, will not work with unconverted lexicons """
        return self._inverseLex.get(wid, None)

    def assignWordId(self, word):
        """Assigns a new word id to the provided word and returns it."""
        # First make sure it's not already in there
        if self._lexicon.has_key(word):
            return self._lexicon[word]


        try: inverse=self._inverseLex
        except AttributeError:
            # woops, old lexicom wo wids
            inverse=self._inverseLex=IOBTree()
            for word, wid in self._lexicon.items():
                inverse[wid]=word

        wid=randid()
        while not inverse.insert(wid, word):
            wid=randid()

        if isinstance(word,StringType):
            self._lexicon[intern(word)] = wid
        else:
            self._lexicon[word] = wid


        return wid


    def get(self, key, default=None):
        """Return the matched word against the key."""
        r=IISet()
        wid=self._lexicon.get(key, default)
        if wid is not None: r.insert(wid)
        return r

    def __getitem__(self, key):
        return self.get(key)


    def __len__(self):
        return len(self._lexicon)


    def Splitter(self, astring, words=None, encoding = "latin1"):
        """ wrap the splitter """
        if words is None: words = self.stop_syn

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


    def query_hook(self, q):
        """ we don't want to modify the query cuz we're dumb """
        return q

stop_words=(
    'am', 'ii', 'iii', 'per', 'po', 're', 'a', 'about', 'above', 'across',
    'after', 'afterwards', 'again', 'against', 'all', 'almost', 'alone',
    'along', 'already', 'also', 'although', 'always', 'am', 'among',
    'amongst', 'amoungst', 'amount', 'an', 'and', 'another', 'any',
    'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'are', 'around',
    'as', 'at', 'back', 'be', 'became', 'because', 'become', 'becomes',
    'becoming', 'been', 'before', 'beforehand', 'behind', 'being',
    'below', 'beside', 'besides', 'between', 'beyond', 'bill', 'both',
    'bottom', 'but', 'by', 'can', 'cannot', 'cant', 'con', 'could',
    'couldnt', 'cry', 'describe', 'detail', 'do', 'done', 'down', 'due',
    'during', 'each', 'eg', 'eight', 'either', 'eleven', 'else',
    'elsewhere', 'empty', 'enough', 'even', 'ever', 'every', 'everyone',
    'everything', 'everywhere', 'except', 'few', 'fifteen', 'fifty',
    'fill', 'find', 'fire', 'first', 'five', 'for', 'former', 'formerly',
    'forty', 'found', 'four', 'from', 'front', 'full', 'further', 'get',
    'give', 'go', 'had', 'has', 'hasnt', 'have', 'he', 'hence', 'her',
    'here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers',
    'herself', 'him', 'himself', 'his', 'how', 'however', 'hundred', 'i',
    'ie', 'if', 'in', 'inc', 'indeed', 'interest', 'into', 'is', 'it',
    'its', 'itself', 'keep', 'last', 'latter', 'latterly', 'least',
    'less', 'made', 'many', 'may', 'me', 'meanwhile', 'might', 'mill',
    'mine', 'more', 'moreover', 'most', 'mostly', 'move', 'much', 'must',
    'my', 'myself', 'name', 'namely', 'neither', 'never', 'nevertheless',
    'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor', 'not',
    'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once',
    'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 'per', 'perhaps',
    'please', 'pre', 'put', 'rather', 're', 'same', 'see', 'seem',
    'seemed', 'seeming', 'seems', 'serious', 'several', 'she', 'should',
    'show', 'side', 'since', 'sincere', 'six', 'sixty', 'so', 'some',
    'somehow', 'someone', 'something', 'sometime', 'sometimes',
    'somewhere', 'still', 'such', 'take', 'ten', 'than', 'that', 'the',
    'their', 'them', 'themselves', 'then', 'thence', 'there',
    'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these',
    'they', 'thick', 'thin', 'third', 'this', 'those', 'though', 'three',
    'through', 'throughout', 'thru', 'thus', 'to', 'together', 'too',
    'toward', 'towards', 'twelve', 'twenty', 'two', 'un', 'under',
    'until', 'up', 'upon', 'us', 'very', 'via', 'was', 'we', 'well',
    'were', 'what', 'whatever', 'when', 'whence', 'whenever', 'where',
    'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon',
    'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever',
    'whole', 'whom', 'whose', 'why', 'will', 'with', 'within', 'without',
    'would', 'yet', 'you', 'your', 'yours', 'yourself', 'yourselves',
    )
stop_word_dict={}
for word in stop_words: stop_word_dict[word]=None
