from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex
from Products.ZCTextIndex.tests \
     import testIndex, testQueryEngine, testQueryParser
from Products.ZCTextIndex.Index import scaled_int, SCALE_FACTOR
from Products.ZCTextIndex.Lexicon import Lexicon, Splitter
from Products.ZCTextIndex.Lexicon import CaseNormalizer, StopWordRemover

import unittest

class Indexable:
    def __init__(self, text):
        self.text = text
        
class LexiconHolder:
    def __init__(self, lexicon):
        self.lexicon = lexicon
        
class Extra:
    pass

# The tests classes below create a ZCTextIndex().  Then they create
# instance variables that point to the internal components used by
# ZCTextIndex.  These tests run the individual module unit tests with
# the fully integrated ZCTextIndex.

def eq(scaled1, scaled2, epsilon=scaled_int(0.01)):
    if abs(scaled1 - scaled2) > epsilon:
        raise AssertionError, "%s != %s" % (scaled1, scaled2)

class IndexTests(testIndex.IndexTest):

    def setUp(self):
        extra = Extra()
        extra.doc_attr = 'text'
        extra.lexicon_id = 'lexicon'
        caller = LexiconHolder(Lexicon(Splitter(), CaseNormalizer(),
                               StopWordRemover()))
        self.zc_index = ZCTextIndex('name', extra, caller)
        self.index = self.zc_index.index
        self.lexicon = self.zc_index.lexicon

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
        self.assertEqual(len(self.index._get_undoinfo(1)), 1)

    def testRanking(self):
        # A fairly involved test of the ranking calculations based on
        # an example set of documents in queries in Managing
        # Gigabytes, pp. 180-188.
        self.words = ["cold", "days", "eat", "hot", "lot", "nine", "old",
                      "pease", "porridge", "pot"]
        self._ranking_index()
        self._ranking_tf()
        self._ranking_idf()
        self._ranking_queries()

    def _ranking_index(self):
        docs = ["Pease porridge hot, pease porridge cold,",
                "Pease porridge in the pot,",
                "Nine days old.",
                "In the pot cold, in the pot hot,",
                "Pease porridge, pease porridge,",
                "Eat the lot."]
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
            q = self.zc_index.parser.parseQuery(raw)
            wq = self.index.query_weight(q.terms())
            eq(wq, scaled_int(wqs[i]))
            r = self.zc_index.query(raw)
            self.assertEqual(len(r), len(results[i]))
            # convert the results to a dict for each checking
            d = {}
            for doc, score in results[i]:
                d[doc] = scaled_int(score)
            for doc, score in r:
                score = scaled_int(float(score / SCALE_FACTOR) / wq)
                self.assert_(0 <= score <= SCALE_FACTOR)
                eq(d[doc], score)

class QueryTests(testQueryEngine.TestQueryEngine,
                 testQueryParser.TestQueryParser):

    # The FauxIndex in testQueryEngine contains four documents.
    # docid 1: foo, bar, ham
    # docid 2: bar, ham
    # docid 3: foo, ham
    # docid 4: ham

    docs = ["foo bar ham", "bar ham", "foo ham", "ham"]

    def setUp(self):
        extra = Extra()
        extra.doc_attr = 'text'
        extra.lexicon_id = 'lexicon'
        caller = LexiconHolder(Lexicon(Splitter(), CaseNormalizer(),
                               StopWordRemover()))
        self.zc_index = ZCTextIndex('name', extra, caller)
        self.p = self.parser = self.zc_index.parser
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
        d = {}
        for k, v in set.items():
            d[k] = v
        self.assertEqual(d.keys(), dict.keys())


def test_suite():
    s = unittest.TestSuite()
    for klass in IndexTests, QueryTests:
        s.addTest(unittest.makeSuite(klass))
    return s

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
