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
"""Lexicon unit tests.

$Id$
"""

import unittest

import os, sys

import ZODB
import transaction

from Products.ZCTextIndex.Lexicon import Lexicon
from Products.ZCTextIndex.Lexicon import Splitter, CaseNormalizer

class StupidPipelineElement:
    def __init__(self, fromword, toword):
        self.__fromword = fromword
        self.__toword = toword

    def process(self, seq):
        res = []
        for term in seq:
            if term == self.__fromword:
                res.append(self.__toword)
            else:
                res.append(term)
        return res

class WackyReversePipelineElement:
    def __init__(self, revword):
        self.__revword = revword

    def process(self, seq):
        res = []
        for term in seq:
            if term == self.__revword:
                x = list(term)
                x.reverse()
                res.append(''.join(x))
            else:
                res.append(term)
        return res

class StopWordPipelineElement:
    def __init__(self, stopdict={}):
        self.__stopdict = stopdict

    def process(self, seq):
        res = []
        for term in seq:
            if self.__stopdict.get(term):
                continue
            else:
                res.append(term)
        return res


class Test(unittest.TestCase):

    def test_z3interfaces(self):
        from Products.ZCTextIndex.interfaces import ILexicon
        from zope.interface.verify import verifyClass

        verifyClass(ILexicon, Lexicon)

    def testSourceToWordIds(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        self.assertEqual(wids, [1, 2, 3])

    def testTermToWordIds(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('dogs')
        self.assertEqual(wids, [3])

    def testMissingTermToWordIds(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('boxes')
        self.assertEqual(wids, [0])

    def testTermToWordIdsWithProcess_post_glob(self):
        """This test is for added process_post_glob"""
        class AddedSplitter(Splitter):
            def process_post_glob(self, lst):
                assert lst == ['dogs']
                return ['dogs']
        lexicon = Lexicon(AddedSplitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('dogs')
        self.assertEqual(wids, [3])

    def testMissingTermToWordIdsWithProcess_post_glob(self):
        """This test is for added process_post_glob"""
        class AddedSplitter(Splitter):
            def process_post_glob(self, lst):
                assert lst == ['dogs']
                return ['fox']
        lexicon = Lexicon(AddedSplitter())
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('dogs')
        self.assertEqual(wids, [0])

    def testOnePipelineElement(self):
        lexicon = Lexicon(Splitter(), StupidPipelineElement('dogs', 'fish'))
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('fish')
        self.assertEqual(wids, [3])

    def testSplitterAdaptorFold(self):
        lexicon = Lexicon(Splitter(), CaseNormalizer())
        wids = lexicon.sourceToWordIds('CATS and dogs')
        wids = lexicon.termToWordIds('cats and dogs')
        self.assertEqual(wids, [1, 2, 3])

    def testSplitterAdaptorNofold(self):
        lexicon = Lexicon(Splitter())
        wids = lexicon.sourceToWordIds('CATS and dogs')
        wids = lexicon.termToWordIds('cats and dogs')
        self.assertEqual(wids, [0, 2, 3])

    def testTwoElementPipeline(self):
        lexicon = Lexicon(Splitter(),
                          StupidPipelineElement('cats', 'fish'),
                          WackyReversePipelineElement('fish'))
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('hsif')
        self.assertEqual(wids, [1])

    def testThreeElementPipeline(self):
        lexicon = Lexicon(Splitter(),
                          StopWordPipelineElement({'and':1}),
                          StupidPipelineElement('dogs', 'fish'),
                          WackyReversePipelineElement('fish'))
        wids = lexicon.sourceToWordIds('cats and dogs')
        wids = lexicon.termToWordIds('hsif')
        self.assertEqual(wids, [2])
        
    def testSplitterLocaleAwareness(self):
        from Products.ZCTextIndex.HTMLSplitter import HTMLWordSplitter
        import locale
        loc = locale.setlocale(locale.LC_ALL) # get current locale
         # set German locale
        try:
            if sys.platform != 'win32':
                locale.setlocale(locale.LC_ALL, 'de_DE.ISO8859-1')
            else:
                locale.setlocale(locale.LC_ALL, 'German_Germany.1252')
        except locale.Error:
            return # This test doesn't work here :-(
        expected = ['m\xfclltonne', 'waschb\xe4r',
                    'beh\xf6rde', '\xfcberflieger']
        words = [" ".join(expected)]
        words = Splitter().process(words)
        self.assertEqual(words, expected)
        words = HTMLWordSplitter().process(words)
        self.assertEqual(words, expected)
        locale.setlocale(locale.LC_ALL, loc) # restore saved locale
        
    def testUpgradeLength(self):
        from BTrees.Length import Length
        lexicon = Lexicon(Splitter())
        del lexicon.length # Older instances don't override length
        lexicon.sourceToWordIds('how now brown cow')
        self.assert_(lexicon.length.__class__ is Length)        
        
class TestLexiconConflict(unittest.TestCase):
    
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
        
    def testAddWordConflict(self):
        self.l = Lexicon(Splitter())
        self.openDB()
        r1 = self.db.open().root()
        r1['l'] = self.l
        transaction.commit()
        
        r2 = self.db.open().root()
        copy = r2['l']
        # Make sure the data is loaded
        list(copy._wids.items())
        list(copy._words.items())
        copy.length()
        
        self.assertEqual(self.l._p_serial, copy._p_serial)
        
        self.l.sourceToWordIds('mary had a little lamb')
        transaction.commit()
        
        copy.sourceToWordIds('whose fleece was')
        copy.sourceToWordIds('white as snow')
        transaction.commit()
        self.assertEqual(copy.length(), 11)
        self.assertEqual(copy.length(), len(copy._words))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(Test))
    suite.addTest(unittest.makeSuite(TestLexiconConflict))
    return suite

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
