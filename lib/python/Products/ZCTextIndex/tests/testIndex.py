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
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

from unittest import TestCase, TestSuite, main, makeSuite

from Products.ZCTextIndex.Lexicon import Lexicon, Splitter
from Products.ZCTextIndex.Index      import Index as CosineIndex
from Products.ZCTextIndex.OkapiIndex import Index as OkapiIndex

# The cosine and Okapi indices have the same public interfaces, but these
# tests access internal attributes, and those aren't identical.
# The IndexTest class is abstract, and subclasses must implement the
# check_docid_known and num_docs_known methods.  CosineIndexTest (later in
# this file) does those in terms of ._docweight, while OkapiIndexTest
# (later in this file) does them in terms of ._doclen.

class IndexTest(TestCase):

    # Subclasses must implement these methods, and set a class variable
    # IndexFactory to the appropriate index object constructor.

    def check_docid_known(self, DOCID):
        raise NotImplementedError

    def num_docs_known(self):
        raise NotImplementedError


    def setUp(self):
        self.lexicon = Lexicon(Splitter())
        self.index = self.IndexFactory(self.lexicon)

    def test_index_document(self, DOCID=1):
        doc = "simple document contains five words"
        self.index.index_doc(DOCID, doc)
        self.check_docid_known(DOCID)
        self.assertEqual(self.num_docs_known(), 1)
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 5)
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_unindex_document(self):
        DOCID = 1
        self.test_index_document(DOCID)
        self.index.unindex_doc(DOCID)
        self.assertEqual(self.num_docs_known(), 0)
        self.assertEqual(len(self.index._wordinfo), 0)
        self.assertEqual(len(self.index._docwords), 0)

    def test_index_two_documents(self):
        self.test_index_document()
        doc = "another document just four"
        DOCID = 2
        self.index.index_doc(DOCID, doc)
        self.check_docid_known(DOCID)
        self.assertEqual(self.num_docs_known(), 2)
        self.assertEqual(len(self.index._wordinfo), 8)
        self.assertEqual(len(self.index._docwords), 2)
        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 4)
        wids = self.lexicon.termToWordIds("document")
        self.assertEqual(len(wids), 1)
        document_wid = wids[0]
        for wid, map in self.index._wordinfo.items():
            if wid == document_wid:
                self.assertEqual(len(map), 2)
                self.assert_(map.has_key(1))
                self.assert_(map.has_key(DOCID))
            else:
                self.assertEqual(len(map), 1)

    def test_index_two_unindex_one(self):
        # index two documents, unindex one, and test the results
        self.test_index_two_documents()
        self.index.unindex_doc(1)
        DOCID = 2
        self.assertEqual(self.num_docs_known(), 1)
        self.check_docid_known(DOCID)
        self.assertEqual(len(self.index._wordinfo), 4)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 4)
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_index_duplicated_words(self, DOCID=1):
        doc = "very simple repeat repeat repeat document test"
        self.index.index_doc(DOCID, doc)
        self.check_docid_known(DOCID)
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index._get_undoinfo(DOCID)), 7)
        wids = self.lexicon.termToWordIds("repeat")
        self.assertEqual(len(wids), 1)
        repititive_wid = wids[0]
        for wid, map in self.index._wordinfo.items():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_simple_query_oneresult(self):
        self.index.index_doc(1, 'not the same document')
        results = self.index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_simple_query_noresults(self):
        self.index.index_doc(1, 'not the same document')
        results = self.index.search("frobnicate")
        self.assertEqual(list(results.keys()), [])

    def test_query_oneresult(self):
        self.index.index_doc(1, 'not the same document')
        self.index.index_doc(2, 'something about something else')
        results = self.index.search("document")
        self.assertEqual(list(results.keys()), [1])

    def test_search_phrase(self):
        self.index.index_doc(1, "the quick brown fox jumps over the lazy dog")
        self.index.index_doc(2, "the quick fox jumps lazy over the brown dog")
        results = self.index.search_phrase("quick brown fox")
        self.assertEqual(list(results.keys()), [1])

    def test_search_glob(self):
        self.index.index_doc(1, "how now brown cow")
        self.index.index_doc(2, "hough nough browne cough")
        self.index.index_doc(3, "bar brawl")
        results = self.index.search_glob("bro*")
        self.assertEqual(list(results.keys()), [1, 2])
        results = self.index.search_glob("b*")
        self.assertEqual(list(results.keys()), [1, 2, 3])

class CosineIndexTest(IndexTest):
    IndexFactory = CosineIndex

    def check_docid_known(self, docid):
        self.assert_(self.index._docweight.has_key(docid))
        self.assert_(self.index._docweight[docid] > 0)

    def num_docs_known(self):
        return len(self.index._docweight)

class OkapiIndexTest(IndexTest):
    IndexFactory = OkapiIndex

    def check_docid_known(self, docid):
        self.assert_(self.index._doclen.has_key(docid))
        self.assert_(self.index._doclen[docid] > 0)

    def num_docs_known(self):
        return len(self.index._doclen)

def test_suite():
    return TestSuite((makeSuite(CosineIndexTest),
                      makeSuite(OkapiIndexTest),
                    ))

if __name__=='__main__':
    main(defaultTest='test_suite')
