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
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZCTextIndex unit tests.

$Id$
"""

import unittest

import re

import Acquisition
from zExceptions import NotFound

from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex, PLexicon
from Products.ZCTextIndex.tests import \
     testIndex, testQueryEngine, testQueryParser
from Products.ZCTextIndex.BaseIndex import \
     scaled_int, SCALE_FACTOR, inverse_doc_frequency
from Products.ZCTextIndex.CosineIndex import CosineIndex
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
from Products.ZCTextIndex.Lexicon import Splitter
from Products.ZCTextIndex.Lexicon import CaseNormalizer, StopWordRemover
from Products.ZCTextIndex.QueryParser import QueryParser
from Products.ZCTextIndex.StopDict import get_stopdict
from Products.ZCTextIndex.ParseTree import ParseError


class Indexable:
    def __init__(self, text):
        self.text = text

class Indexable2:
    def __init__(self, text1, text2):
        self.text1 = text1
        self.text2 = text2

class LexiconHolder(Acquisition.Implicit):
    def __init__(self, lexicon):
        self.lexicon = lexicon

    def getPhysicalPath(self):
        return ('',) # Pretend to be the root

def dummyUnrestrictedTraverse(self, path):
    if path == ('', 'lexicon',):
        return self.lexicon
    raise NotFound, path

# The tests classes below create a ZCTextIndex().  Then they create
# instance variables that point to the internal components used by
# ZCTextIndex.  These tests run the individual module unit tests with
# the fully integrated ZCTextIndex.

def eq(scaled1, scaled2, epsilon=scaled_int(0.01)):
    if abs(scaled1 - scaled2) > epsilon:
        raise AssertionError, "%s != %s" % (scaled1, scaled2)

# A series of text chunks to use for the re-index tests (testDocUpdate).
text = [
    """Here's a knocking indeed! If a
    man were porter of hell-gate, he should have
    old turning the key.  knock (that made sure
    sure there's at least one word in common)."""

    """Knock,
    knock, knock! Who's there, i' the name of
    Beelzebub? Here's a farmer, that hanged
    himself on the expectation of plenty: come in
    time; have napkins enow about you; here
    you'll sweat for't.""",

    """Knock,
    knock! Who's there, in the other devil's
    name? Faith, here's an equivocator, that could
    swear in both the scales against either scale;
    who committed treason enough for God's sake,
    yet could not equivocate to heaven: O, come
    in, equivocator.""",

    """Knock,
    knock, knock! Who's there? Faith, here's an
    English tailor come hither, for stealing out of
    a French hose: come in, tailor; here you may
    roast your goose.""",

    """Knock,
    knock; never at quiet! What are you? But
    this place is too cold for hell. I'll devil-porter
    it no further: I had thought to have let in
    some of all professions that go the primrose
    way to the everlasting bonfire."""
]

# Subclasses should derive from one of testIndex.{CosineIndexTest,
# OkapiIndexTest} too.

class ZCIndexTestsBase:

    def setUp(self):
        self.lexicon = PLexicon('lexicon', '',
                                Splitter(),
                                CaseNormalizer(),
                                StopWordRemover())
        caller = LexiconHolder(self.lexicon)
        self.zc_index = ZCTextIndex('name',
                                    None,
                                    caller,
                                    self.IndexFactory,
                                    'text',
                                    'lexicon')
        self.index = self.zc_index.index


    def parserFailure(self, query):
        self.assertRaises(ParseError, self.zc_index.query, query)

    def parserSuccess(self, query, n):
        r, num = self.zc_index.query(query)
        self.assertEqual(num, n)
        if n:
            self.assertEqual(r[0][0], 1)

    def testMultipleAttributes(self):
        lexicon = PLexicon('lexicon', '',
                            Splitter(),
                            CaseNormalizer(),
                            StopWordRemover())
        caller = LexiconHolder(self.lexicon)
        zc_index = ZCTextIndex('name',
                                None,
                                caller,
                                self.IndexFactory,
                               'text1,text2',
                               'lexicon')
        doc = Indexable2('foo bar', 'alpha omega')
        zc_index.index_object(1, doc)
        nbest, total = zc_index.query('foo')
        self.assertEqual(len(nbest), 1)
        nbest, total = zc_index.query('foo alpha')
        self.assertEqual(len(nbest), 1)
        nbest, total = zc_index.query('foo alpha gamma')
        self.assertEqual(len(nbest), 0)

    def testListAttributes(self):
        lexicon = PLexicon('lexicon', '',
                            Splitter(),
                            CaseNormalizer(),
                            StopWordRemover())
        caller = LexiconHolder(self.lexicon)
        zc_index = ZCTextIndex('name',
                                None,
                                caller,
                                self.IndexFactory,
                               'text1,text2',
                               'lexicon')
        doc = Indexable2('Hello Tim', \
                         ['Now is the winter of our discontent',
                          'Made glorious summer by this sun of York', ])
        zc_index.index_object(1, doc)
        nbest, total = zc_index.query('glorious')
        self.assertEqual(len(nbest), 1)
        nbest, total = zc_index.query('York Tim')
        self.assertEqual(len(nbest), 1)
        nbest, total = zc_index.query('Tuesday Tim York')
        self.assertEqual(len(nbest), 0)

    def testStopWords(self):
        # the only non-stopword is question
        text = ("to be or not to be "
                "that is the question")
        doc = Indexable(text)
        self.zc_index.index_object(1, doc)
        for word in text.split():
            if word != "question":
                wids = self.lexicon.termToWordIds(word)
                self.assertEqual(wids, [])
        self.assertEqual(len(self.index.get_words(1)), 1)

        self.parserSuccess('question', 1)
        self.parserSuccess('question AND to AND be', 1)
        self.parserSuccess('to AND question AND be', 1)
        self.parserSuccess('question AND NOT gardenia', 1)
        self.parserSuccess('question AND gardenia', 0)
        self.parserSuccess('gardenia', 0)
        self.parserSuccess('question OR gardenia', 1)
        self.parserSuccess('question AND NOT to AND NOT be', 1)
        self.parserSuccess('question OR to OR be', 1)
        self.parserSuccess('question to be', 1)

        self.parserFailure('to be')
        self.parserFailure('to AND be')
        self.parserFailure('to OR be')
        self.parserFailure('to AND NOT be')
        self.parserFailure('to AND NOT question')
        self.parserFailure('to AND NOT gardenia')

    def testDocUpdate(self):
        docid = 1   # doesn't change -- we index the same doc repeatedly
        N = len(text)
        stop = get_stopdict()

        d = {} # word -> list of version numbers containing that word
        for version, i in zip(text, range(N)):
            # use a simple splitter rather than an official one
            words = [w for w in re.split("\W+", version.lower())
                     if len(w) > 1 and not stop.has_key(w)]
            word_seen = {}
            for w in words:
                if not word_seen.has_key(w):
                    d.setdefault(w, []).append(i)
                    word_seen[w] = 1

        unique = {} # version number -> list of words unique to that version
        common = [] # list of words common to all versions
        for w, versionlist in d.items():
            if len(versionlist) == 1:
                unique.setdefault(versionlist[0], []).append(w)
            elif len(versionlist) == N:
                common.append(w)
        self.assert_(len(common) > 0)
        self.assert_(len(unique) > 0)

        for version, i in zip(text, range(N)):
            doc = Indexable(version)
            self.zc_index.index_object(docid, doc)
            for w in common:
                nbest, total = self.zc_index.query(w)
                self.assertEqual(total, 1, "did not find %s" % w)
            for k, v in unique.items():
                if k == i:
                    continue
                for w in v:
                    nbest, total = self.zc_index.query(w)
                    self.assertEqual(total, 0, "did not expect to find %s" % w)


class CosineIndexTests(ZCIndexTestsBase, testIndex.CosineIndexTest):

    # A fairly involved test of the ranking calculations based on
    # an example set of documents in queries in Managing
    # Gigabytes, pp. 180-188.  This test peeks into many internals of the
    # cosine indexer.

    def test_z3interfaces(self):
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.ZCTextIndex.interfaces import IZCTextIndex
        from zope.interface.verify import verifyClass

        verifyClass(IPluggableIndex, ZCTextIndex)
        verifyClass(IZCTextIndex, ZCTextIndex)

    def testRanking(self):
        self.words = ["cold", "days", "eat", "hot", "lot", "nine", "old",
                      "pease", "porridge", "pot"]
        self.docs = ["Pease porridge hot, pease porridge cold,",
                     "Pease porridge in the pot,",
                     "Nine days old.",
                     "In the pot cold, in the pot hot,",
                     "Pease porridge, pease porridge,",
                     "Eat the lot."]
        self._ranking_index()
        self._ranking_tf()
        self._ranking_idf()
        self._ranking_queries()

        # A digression to exercise re-indexing.
        docs = self.docs
        for variant in "hot cold porridge python", "pease hot pithy":
            self.zc_index.index_object(len(docs), Indexable(variant))
            try:
                self._ranking_tf()
            except (AssertionError, KeyError):
                pass
            else:
                self.fail("expected _ranking_tf() to fail -- reindex")

            try:
                self._ranking_idf()
            except (AssertionError, KeyError):
                pass
            else:
                self.fail("expected _ranking_idf() to fail -- reindex")

            try:
                self._ranking_queries()
            except AssertionError:
                pass
            else:
                self.fail("expected _ranking_queries() to fail -- reindex")

        # This should leave things exactly as they were.
        self.zc_index.index_object(len(docs), Indexable(docs[-1]))
        self._ranking_tf()
        self._ranking_idf()
        self._ranking_queries()

    def _ranking_index(self):
        docs = self.docs
        for i in range(len(docs)):
            self.zc_index.index_object(i + 1, Indexable(docs[i]))

    def _ranking_tf(self):
        # matrix of term weights for the rows are docids
        # and the columns are indexes into this list:
        l_wdt = [(1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.7, 1.7, 0.0),
               (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0),
               (0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0),
               (1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.7),
               (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.7, 1.7, 0.0),
               (0.0, 0.0, 1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0)]
        l_Wd = [2.78, 1.73, 1.73, 2.21, 2.39, 1.41]

        for i in range(len(l_Wd)):
            docid = i + 1
            scaled_Wd = scaled_int(l_Wd[i])
            eq(scaled_Wd, self.index._get_Wd(docid))
            wdts = [scaled_int(t) for t in l_wdt[i]]
            for j in range(len(wdts)):
                wdt = self.index._get_wdt(docid, self.words[j])
                eq(wdts[j], wdt)

    def _ranking_idf(self):
        word_freqs = [2, 1, 1, 2, 1, 1, 1, 3, 3, 2]
        idfs = [1.39, 1.95, 1.95, 1.39, 1.95, 1.95, 1.95, 1.10, 1.10, 1.39]
        for i in range(len(self.words)):
            word = self.words[i]
            eq(word_freqs[i], self.index._get_ft(word))
            eq(scaled_int(idfs[i]), self.index._get_wt(word))

    def _ranking_queries(self):
        queries = ["eat", "porridge", "hot OR porridge",
                   "eat OR nine OR day OR old OR porridge"]
        wqs = [1.95, 1.10, 1.77, 3.55]
        results = [[(6, 0.71)],
                   [(1, 0.61), (2, 0.58), (5, 0.71)],
                   [(1, 0.66), (2, 0.36), (4, 0.36), (5, 0.44)],
                   [(1, 0.19), (2, 0.18), (3, 0.63), (5, 0.22), (6, 0.39)]]
        for i in range(len(queries)):
            raw = queries[i]
            q = QueryParser(self.lexicon).parseQuery(raw)
            wq = self.index.query_weight(q.terms())
            eq(wq, scaled_int(wqs[i]))
            r, n = self.zc_index.query(raw)
            self.assertEqual(len(r), len(results[i]))
            # convert the results to a dict for each checking
            d = {}
            for doc, score in results[i]:
                d[doc] = scaled_int(score)
            for doc, score in r:
                score = scaled_int(float(score / SCALE_FACTOR) / wq)
                self.assert_(0 <= score <= SCALE_FACTOR)
                eq(d[doc], score)

class OkapiIndexTests(ZCIndexTestsBase, testIndex.OkapiIndexTest):

    # A white-box test.
    def testAbsoluteScores(self):
        docs = ["one",
                "one two",
                "one two three"]

        for i in range(len(docs)):
            self.zc_index.index_object(i + 1, Indexable(docs[i]))

        self._checkAbsoluteScores()

        # Exercise re-indexing.
        for variant in "one xyz", "xyz two three", "abc def":
            self.zc_index.index_object(len(docs), Indexable(variant))
            try:
                self._checkAbsoluteScores()
            except AssertionError:
                pass
            else:
                self.fail("expected _checkAbsoluteScores() to fail -- reindex")
        # This should leave things exactly as they were.
        self.zc_index.index_object(len(docs), Indexable(docs[-1]))
        self._checkAbsoluteScores()

    def _checkAbsoluteScores(self):
        self.assertEqual(self.index._totaldoclen(), 6)
        # So the mean doc length is 2.  We use that later.

        r, num = self.zc_index.query("one")
        self.assertEqual(num, 3)
        self.assertEqual(len(r), 3)

        # Because our Okapi's B parameter is > 0, and "one" only appears
        # once in each doc, the verbosity hypothesis favors shorter docs.
        self.assertEqual([doc for doc, score in r], [1, 2, 3])

        # The way the Okapi math works, a word that appears exactly once in
        # an average (length) doc gets tf score 1.  Our second doc has
        # an average length, so its score should by 1 (tf) times the
        # inverse doc frequency of "one".  But "one" appears in every
        # doc, so its IDF is log(1 + 3/3) = log(2).
        self.assertEqual(r[1][1], scaled_int(inverse_doc_frequency(3, 3)))

        # Similarly for "two".
        r, num = self.zc_index.query("two")
        self.assertEqual(num, 2)
        self.assertEqual(len(r), 2)
        self.assertEqual([doc for doc, score in r], [2, 3])
        self.assertEqual(r[0][1], scaled_int(inverse_doc_frequency(2, 3)))

        # And "three", except that doesn't appear in an average-size doc, so
        # the math is much more involved.
        r, num = self.zc_index.query("three")
        self.assertEqual(num, 1)
        self.assertEqual(len(r), 1)
        self.assertEqual([doc for doc, score in r], [3])
        idf = inverse_doc_frequency(1, 3)
        meandoclen = 2.0
        lengthweight = 1.0 - OkapiIndex.B + OkapiIndex.B * 3 / meandoclen
        tf = (1.0 + OkapiIndex.K1) / (1.0 + OkapiIndex.K1 * lengthweight)
        self.assertEqual(r[0][1], scaled_int(tf * idf))

    # More of a black-box test, but based on insight into how Okapi is trying
    # to think.
    def testRelativeScores(self):
        # Create 9 10-word docs.
        # All contain one instance of "one".
        # Doc #i contains i instances of "two" and 9-i of "xyz".
        for i in range(1, 10):
            doc = "one " + "two " * i + "xyz " * (9 - i)
            self.zc_index.index_object(i, Indexable(doc))
        self._checkRelativeScores()

        # Exercise re-indexing.
        self.zc_index.index_object(9, Indexable("two xyz"))
        try:
            self._checkRelativeScores()
        except AssertionError:
            pass
        else:
            self.fail("expected _checkRelativeScores() to fail after reindex")
        # This should leave things exactly as they were.
        self.zc_index.index_object(9, Indexable(doc))
        self._checkRelativeScores()

    def _checkRelativeScores(self):
        r, num = self.zc_index.query("one two")
        self.assertEqual(num, 9)
        self.assertEqual(len(r), 9)
        # The more twos in a doc, the better the score should be.
        self.assertEqual([doc for doc, score in r], range(9, 0, -1))

        # Search for "two" alone shouldn't make any difference to relative
        # results.
        r, num = self.zc_index.query("two")
        self.assertEqual(num, 9)
        self.assertEqual(len(r), 9)
        self.assertEqual([doc for doc, score in r], range(9, 0, -1))

        # Searching for xyz should skip doc 9, and favor the lower-numbered
        # docs (they have more instances of xyz).
        r, num = self.zc_index.query("xyz")
        self.assertEqual(num, 8)
        self.assertEqual(len(r), 8)
        self.assertEqual([doc for doc, score in r], range(1, 9))

        # And relative results shouldn't change if we add "one".
        r, num = self.zc_index.query("xyz one")
        self.assertEqual(num, 8)
        self.assertEqual(len(r), 8)
        self.assertEqual([doc for doc, score in r], range(1, 9))

        # But if we search for all the words, it's much muddier.  The boost
        # in going from i instances to i+1 of a given word is smaller than
        # the boost in going from i-1 to i, so the winner will be the one
        # that balances the # of twos and xyzs best.  But the test is nasty
        # that way:  doc 4 has 4 two and 5 xyz, while doc 5 has the reverse.
        # However, xyz is missing from doc 9, so xyz has a larger idf than
        # two has.  Since all the doc lengths are the same, doc lengths don't
        # matter.  So doc 4 should win, and doc 5 should come in second.
        # The loser will be the most unbalanced, but is that doc 1 (1 two 8
        # xyz) or doc 8 (8 two 1 xyz)?  Again xyz has a higher idf, so doc 1
        # is more valuable, and doc 8 is the loser.
        r, num = self.zc_index.query("xyz one two")
        self.assertEqual(num, 8)
        self.assertEqual(len(r), 8)
        self.assertEqual(r[0][0], 4)    # winner
        self.assertEqual(r[1][0], 5)    # runner up
        self.assertEqual(r[-1][0], 8)   # loser
        self.assertEqual(r[-2][0], 1)   # penultimate loser

        # And nothing about the relative results in the last test should
        # change if we leave "one" out of the search (it appears in all
        # docs, so it's a wash).
        r, num = self.zc_index.query("two xyz")
        self.assertEqual(num, 8)
        self.assertEqual(len(r), 8)
        self.assertEqual(r[0][0], 4)    # winner
        self.assertEqual(r[1][0], 5)    # runner up
        self.assertEqual(r[-1][0], 8)   # loser
        self.assertEqual(r[-2][0], 1)   # penultimate loser


############################################################################
# Subclasses of QueryTestsBase must set a class variable IndexFactory to
# the kind of index to be constructed.

class QueryTestsBase(testQueryEngine.TestQueryEngine,
                     testQueryParser.TestQueryParser):

    # The FauxIndex in testQueryEngine contains four documents.
    # docid 1: foo, bar, ham
    # docid 2: bar, ham
    # docid 3: foo, ham
    # docid 4: ham

    docs = ["foo bar ham", "bar ham", "foo ham", "ham"]

    def setUp(self):
        self.lexicon = PLexicon('lexicon', '',
                                Splitter(),
                                CaseNormalizer(),
                                StopWordRemover())
        caller = LexiconHolder(self.lexicon)

        self.zc_index = ZCTextIndex('name',
                                    None,
                                    caller,
                                    self.IndexFactory,
                                    'text',
                                    'lexicon')
        self.parser = QueryParser(self.lexicon)
        self.index = self.zc_index.index
        self.add_docs()

    def add_docs(self):
        for i in range(len(self.docs)):
            text = self.docs[i]
            obj = Indexable(text)
            self.zc_index.index_object(i + 1, obj)

    def compareSet(self, set, dict):
        # XXX The FauxIndex and the real Index score documents very
        # differently.  The set comparison can't actually compare the
        # items, but it can compare the keys.  That will have to do for now.
        setkeys = list(set.keys())
        dictkeys = dict.keys()
        setkeys.sort()
        dictkeys.sort()
        self.assertEqual(setkeys, dictkeys)


class CosineQueryTests(QueryTestsBase):
    IndexFactory = CosineIndex


class OkapiQueryTests(QueryTestsBase):
    IndexFactory = OkapiIndex


class PLexiconTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.ZCTextIndex.ZCTextIndex import PLexicon
        return PLexicon

    def _makeOne(self, id='testing', title='Testing', *pipeline):
        return self._getTargetClass()(id, title, *pipeline)

    def test_class_conforms_to_ILexicon(self):
        from Products.ZCTextIndex.interfaces import ILexicon
        from zope.interface.verify import verifyClass
        verifyClass(ILexicon, self._getTargetClass())

    def test_instance_conforms_to_ILexicon(self):
        from Products.ZCTextIndex.interfaces import ILexicon
        from zope.interface.verify import verifyObject
        verifyObject(ILexicon, self._makeOne())

    def test_class_conforms_to_IZCLexicon(self):
        from Products.ZCTextIndex.interfaces import IZCLexicon
        from zope.interface.verify import verifyClass
        verifyClass(IZCLexicon, self._getTargetClass())

    def test_instance_conforms_to_IZCLexicon(self):
        from Products.ZCTextIndex.interfaces import IZCLexicon
        from zope.interface.verify import verifyObject
        verifyObject(IZCLexicon, self._makeOne())

    def test_queryLexicon_defaults_empty(self):
        lexicon = self._makeOne()
        info = lexicon.queryLexicon(REQUEST=None, words=None)
        self.assertEqual(info['page'], 0)
        self.assertEqual(info['rows'], 20)
        self.assertEqual(info['cols'], 4)
        self.assertEqual(info['start_word'], 1)
        self.assertEqual(info['end_word'], 0)
        self.assertEqual(info['word_count'], 0)
        self.assertEqual(list(info['page_range']), [])
        self.assertEqual(info['page_columns'], [])

    def test_queryLexicon_defaults_non_empty(self):
        WORDS = 'aaa bbb ccc ddd eee fff ggg'.split()
        lexicon = self._makeOne()
        lexicon.sourceToWordIds(WORDS)
        info = lexicon.queryLexicon(REQUEST=None, words=None)
        self.assertEqual(info['page'], 0)
        self.assertEqual(info['rows'], 20)
        self.assertEqual(info['cols'], 4)
        self.assertEqual(info['start_word'], 1)
        self.assertEqual(info['end_word'], 7)
        self.assertEqual(info['word_count'], 7)
        self.assertEqual(list(info['page_range']), [0])
        self.assertEqual(info['page_columns'], [WORDS])

    def test_queryLexicon_row_breaks(self):
        WORDS = 'aaa bbb ccc ddd eee fff ggg'.split()
        lexicon = self._makeOne()
        lexicon.sourceToWordIds(WORDS)
        info = lexicon.queryLexicon(REQUEST=None, words=None, rows=4)
        self.assertEqual(info['page'], 0)
        self.assertEqual(info['rows'], 4)
        self.assertEqual(info['cols'], 4)
        self.assertEqual(info['start_word'], 1)
        self.assertEqual(info['end_word'], 7)
        self.assertEqual(info['word_count'], 7)
        self.assertEqual(list(info['page_range']), [0])
        self.assertEqual(info['page_columns'], [WORDS[0:4], WORDS[4:]])

    def test_queryLexicon_page_breaks(self):
        WORDS = 'aaa bbb ccc ddd eee fff ggg'.split()
        lexicon = self._makeOne()
        lexicon.sourceToWordIds(WORDS)
        info = lexicon.queryLexicon(REQUEST=None, words=None, rows=2, cols=2)
        self.assertEqual(info['page'], 0)
        self.assertEqual(info['rows'], 2)
        self.assertEqual(info['cols'], 2)
        self.assertEqual(info['start_word'], 1)
        self.assertEqual(info['end_word'], 4)
        self.assertEqual(info['word_count'], 7)
        self.assertEqual(list(info['page_range']), [0, 1])
        self.assertEqual(info['page_columns'], [WORDS[0:2], WORDS[2:4]])

    def test_queryLexicon_page_break_not_first(self):
        WORDS = 'aaa bbb ccc ddd eee fff ggg'.split()
        lexicon = self._makeOne()
        lexicon.sourceToWordIds(WORDS)
        info = lexicon.queryLexicon(REQUEST=None, words=None,
                                    page=1, rows=2, cols=2)
        self.assertEqual(info['page'], 1)
        self.assertEqual(info['rows'], 2)
        self.assertEqual(info['cols'], 2)
        self.assertEqual(info['start_word'], 5)
        self.assertEqual(info['end_word'], 7)
        self.assertEqual(info['word_count'], 7)
        self.assertEqual(list(info['page_range']), [0, 1])
        self.assertEqual(info['page_columns'], [WORDS[4:6], WORDS[6:]])

    def test_queryLexicon_words_no_globbing(self):
        WORDS = 'aaa bbb ccc ddd eee fff ggg'.split()
        lexicon = self._makeOne()
        lexicon.sourceToWordIds(WORDS)
        info = lexicon.queryLexicon(REQUEST=None, words=['aaa', 'bbb'])
        self.assertEqual(info['page'], 0)
        self.assertEqual(info['rows'], 20)
        self.assertEqual(info['cols'], 4)
        self.assertEqual(info['start_word'], 1)
        self.assertEqual(info['end_word'], 2)
        self.assertEqual(info['word_count'], 2)
        self.assertEqual(list(info['page_range']), [0])
        self.assertEqual(info['page_columns'], [['aaa', 'bbb']])

    def test_queryLexicon_words_w_globbing(self):
        WORDS = 'aaa bbb ccc ddd eee fff ggg'.split()
        lexicon = self._makeOne()
        lexicon.sourceToWordIds(WORDS)
        info = lexicon.queryLexicon(REQUEST=None, words=['aa*', 'bbb*'])
        self.assertEqual(info['page'], 0)
        self.assertEqual(info['rows'], 20)
        self.assertEqual(info['cols'], 4)
        self.assertEqual(info['start_word'], 1)
        self.assertEqual(info['end_word'], 2)
        self.assertEqual(info['word_count'], 2)
        self.assertEqual(list(info['page_range']), [0])
        self.assertEqual(info['page_columns'], [['aaa', 'bbb']])

    def test_queryLexicon_uses_pipeline_for_normalization(self):
        from Products.ZCTextIndex.Lexicon import CaseNormalizer
        WORDS = 'aaa bbb ccc ddd eee fff ggg'.split()
        lexicon = self._makeOne('test', 'Testing', CaseNormalizer())
        lexicon.sourceToWordIds(WORDS)
        info = lexicon.queryLexicon(REQUEST=None, words=['AA*', 'Bbb*'])
        self.assertEqual(info['page'], 0)
        self.assertEqual(info['rows'], 20)
        self.assertEqual(info['cols'], 4)
        self.assertEqual(info['start_word'], 1)
        self.assertEqual(info['end_word'], 2)
        self.assertEqual(info['word_count'], 2)
        self.assertEqual(list(info['page_range']), [0])
        self.assertEqual(info['page_columns'], [['aaa', 'bbb']])


def test_suite():
    s = unittest.TestSuite()
    for klass in (CosineIndexTests, OkapiIndexTests,
                  CosineQueryTests, OkapiQueryTests, PLexiconTests):
        s.addTest(unittest.makeSuite(klass))
    return s

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
