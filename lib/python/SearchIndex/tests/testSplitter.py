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
import unittest

from SearchIndex.Splitter import Splitter

class Tests(unittest.TestCase):
   def testSplitNormalText(self):
       text = 'this is a long string of words'
       a = Splitter(text)
       r = map(None, a)
       assert r == ['this', 'is', 'long', 'string', 'of', 'words']

   def testDropNumeric(self):
       text = '123 456 789 foobar without you nothing'
       a = Splitter(text)
       r = map(None, a)
       assert r == ['foobar', 'without', 'you', 'nothing'], r
       
   def testDropSingleLetterWords(self):
       text = 'without you I nothing'
       a = Splitter(text)
       r = map(None, a)
       assert r == ['without', 'you', 'nothing'], r
       
   def testSplitOnNonAlpha(self):
       text = 'without you I\'m nothing'
       a = Splitter(text)
       r = map(None, a)
       assert r == ['without', 'you', 'nothing'], r
       
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Tests),
        ))

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
