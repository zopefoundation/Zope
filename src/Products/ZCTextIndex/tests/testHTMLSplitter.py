##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
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
"""Test zope.index.text.htmlsplitter
"""
import unittest

class HTMLWordSplitterTests(unittest.TestCase):
    # Subclasses must define '_getBTreesFamily'
    def _getTargetClass(self):
        from Products.ZCTextIndex.HTMLSplitter import HTMLWordSplitter
        return HTMLWordSplitter

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_ISplitter(self):
        from zope.interface.verify import verifyClass
        from Products.ZCTextIndex.interfaces import ISplitter
        verifyClass(ISplitter, self._getTargetClass())

    def test_instance_conforms_to_ISplitter(self):
        from zope.interface.verify import verifyObject
        from Products.ZCTextIndex.interfaces import ISplitter
        verifyObject(ISplitter, self._makeOne())

    def test_process_empty_string(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.process(['']), [])

    def test_process_no_markup(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.process(['abc def']), ['abc', 'def'])

    def test_process_w_markup(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.process(['<h1>abc</h1> &nbsp; <p>def</p>']),
                         ['abc', 'def'])

    def test_process_no_markup_w_glob(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.process(['abc?def hij*klm nop* qrs?']),
                         ['abc', 'def', 'hij', 'klm', 'nop', 'qrs'])

    def test_processGlob_empty_string(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.processGlob(['']), [])

    def test_processGlob_no_markup_no_glob(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.processGlob(['abc def']), ['abc', 'def'])

    def test_processGlob_w_markup_no_glob(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.processGlob(['<h1>abc</h1> &nbsp; '
                                               '<p>def</p>']),
                         ['abc', 'def'])

    def test_processGlob_no_markup_w_glob(self):
        splitter = self._makeOne()
        self.assertEqual(splitter.processGlob(['abc?def hij*klm nop* qrs?']),
                         ['abc?def', 'hij*klm', 'nop*', 'qrs?'])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(HTMLWordSplitterTests),
    ))
