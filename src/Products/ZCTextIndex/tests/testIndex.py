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

import os
from unittest import TestCase, TestSuite, main, makeSuite

import transaction

from BTrees.Length import Length
from Products.ZCTextIndex.Lexicon import Lexicon, Splitter
from Products.ZCTextIndex.CosineIndex import CosineIndex
from Products.ZCTextIndex.OkapiIndex import OkapiIndex

# Subclasses must set a class variable IndexFactory to the appropriate
# index object constructor.

class IndexTest(TestCase):

    def setUp(self):
        self.lexicon = Lexicon(Splitter())
        self.index = self.IndexFactory(self.lexicon)

    def test_index_document(self, DOCID=1):
        doc = "simple document contains five words"
        self.assert_(not self.index.has_doc(DOCID))
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index.has_doc(DOCID))
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._docweight), 1)
        self.assertEqual(
            len(self.index._docweight), self.index.document_count())
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index.get_words(DOCID)), 5)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.length())
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_unindex_document(self):
        DOCID = 1
        self.test_index_document(DOCID)
        self.index.unindex_doc(DOCID)
        self.assertEqual(len(self.index._docweight), 0)
        self.assertEqual(
            len(self.index._docweight), self.index.document_count())
        self.assertEqual(len(self.index._wordinfo), 0)
        self.assertEqual(len(self.index._docwords), 0)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.length())

    def test_index_two_documents(self):
        self.test_index_document()
        doc = "another document just four"
        DOCID = 2
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._docweight), 2)
        self.assertEqual(
            len(self.index._docweight), self.index.document_count())
        self.assertEqual(len(self.index._wordinfo), 8)
        self.assertEqual(len(self.index._docwords), 2)
        self.assertEqual(len(self.index.get_words(DOCID)), 4)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.length())
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
        self.assertEqual(len(self.index._docweight), 1)
        self.assertEqual(
            len(self.index._docweight), self.index.document_count())
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 4)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index.get_words(DOCID)), 4)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.length())
        for map in self.index._wordinfo.values():
            self.assertEqual(len(map), 1)
            self.assert_(map.has_key(DOCID))

    def test_index_duplicated_words(self, DOCID=1):
        doc = "very simple repeat repeat repeat document test"
        self.index.index_doc(DOCID, doc)
        self.assert_(self.index._docweight[DOCID])
        self.assertEqual(len(self.index._wordinfo), 5)
        self.assertEqual(len(self.index._docwords), 1)
        self.assertEqual(len(self.index.get_words(DOCID)), 7)
        self.assertEqual(len(self.index._wordinfo),
                         self.index.length())
        self.assertEqual(
            len(self.index._docweight), self.index.document_count())
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

class OkapiIndexTest(IndexTest):
    IndexFactory = OkapiIndex

class TestIndexConflict(TestCase):
    
    db = None

    def tearDown(self):
        if self.db is not None:
            self.db.close()
            self.storage.cleanup()

    def openDB(self):
        from ZODB.FileStorage import FileStorage
        from ZODB.DB import DB
        n = 'fs_tmp__%s' % os.getpid()
        self.storage = FileStorage(n)
        self.db = DB(self.storage)
        
    def test_index_doc_conflict(self):
        self.index = OkapiIndex(Lexicon())
        self.openDB()
        r1 = self.db.open().root()
        r1['i'] = self.index
        transaction.commit()
        
        r2 = self.db.open().root()
        copy = r2['i']
        # Make sure the data is loaded
        list(copy._docweight.items())
        list(copy._docwords.items())
        list(copy._wordinfo.items())
        list(copy._lexicon._wids.items())
        list(copy._lexicon._words.items())
        
        self.assertEqual(self.index._p_serial, copy._p_serial)
        
        self.index.index_doc(0, 'The time has come')
        transaction.commit()
        
        copy.index_doc(1, 'That time has gone')
        transaction.commit()

    def test_reindex_doc_conflict(self):
        self.index = OkapiIndex(Lexicon())
        self.index.index_doc(0, 'Sometimes change is good')
        self.index.index_doc(1, 'Then again, who asked')
        self.openDB()
        r1 = self.db.open().root()
        r1['i'] = self.index
        transaction.commit()
        
        r2 = self.db.open().root()
        copy = r2['i']
        # Make sure the data is loaded
        list(copy._docweight.items())
        list(copy._docwords.items())
        list(copy._wordinfo.items())
        list(copy._lexicon._wids.items())
        list(copy._lexicon._words.items())
        
        self.assertEqual(self.index._p_serial, copy._p_serial)
        
        self.index.index_doc(0, 'Sometimes change isn\'t bad')
        transaction.commit()
        
        copy.index_doc(1, 'Then again, who asked you?')
        transaction.commit()
        
class TestUpgrade(TestCase):

    def test_query_before_totaldoclen_upgrade(self):
        self.index1 = OkapiIndex(Lexicon(Splitter()))
        self.index1.index_doc(0, 'The quiet of night')
        # Revert index1 back to a long to simulate an older index instance
        self.index1._totaldoclen = long(self.index1._totaldoclen())
        self.assertEqual(len(self.index1.search('night')), 1)
    
    def test_upgrade_totaldoclen(self):
        self.index1 = OkapiIndex(Lexicon())
        self.index2 = OkapiIndex(Lexicon())
        self.index1.index_doc(0, 'The quiet of night')
        self.index2.index_doc(0, 'The quiet of night')
        # Revert index1 back to a long to simulate an older index instance
        self.index1._totaldoclen = long(self.index1._totaldoclen())
        self.index1.index_doc(1, 'gazes upon my shadow')
        self.index2.index_doc(1, 'gazes upon my shadow')
        self.assertEqual(
            self.index1._totaldoclen(), self.index2._totaldoclen())
        self.index1._totaldoclen = long(self.index1._totaldoclen())
        self.index1.unindex_doc(0)
        self.index2.unindex_doc(0)
        self.assertEqual(
            self.index1._totaldoclen(), self.index2._totaldoclen())

    def test_query_before_document_count_upgrade(self):
        self.index1 = OkapiIndex(Lexicon(Splitter()))
        self.index1.index_doc(0, 'The quiet of night')
        # Revert index1 back to a long to simulate an older index instance
        del self.index1.document_count
        self.assertEqual(len(self.index1.search('night')), 1)
    
    def test_upgrade_document_count(self):
        self.index1 = OkapiIndex(Lexicon())
        self.index2 = OkapiIndex(Lexicon())
        self.index1.index_doc(0, 'The quiet of night')
        self.index2.index_doc(0, 'The quiet of night')
        # Revert index1 back to simulate an older index instance
        del self.index1.document_count
        self.index1.index_doc(1, 'gazes upon my shadow')
        self.index2.index_doc(1, 'gazes upon my shadow')
        self.assert_(self.index1.document_count.__class__ is Length)
        self.assertEqual(
            self.index1.document_count(), self.index2.document_count())
        del self.index1.document_count
        self.index1.unindex_doc(0)
        self.index2.unindex_doc(0)
        self.assert_(self.index1.document_count.__class__ is Length)
        self.assertEqual(
            self.index1.document_count(), self.index2.document_count())
        
        
        
def test_suite():
    return TestSuite((makeSuite(CosineIndexTest),
                      makeSuite(OkapiIndexTest),
                      makeSuite(TestIndexConflict),
                      makeSuite(TestUpgrade),
                    ))

if __name__=='__main__':
    main(defaultTest='test_suite')
