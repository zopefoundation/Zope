import unittest
from reStructuredText import HTML

class TestReST(unittest.TestCase):

    def testRoman(self):
        # Make sure we can import the rst parser
        from docutils.parsers import rst

    def testWithSingleSubtitle(self):
        input = '''
title
-----
subtitle
++++++++
text
'''     
        expected='''<h3 class="title">title</h3>
<h4 class="subtitle">subtitle</h4>
<p>text</p>
'''
        output = HTML(input)     
        self.assertEquals(output, expected) 

def test_suite():
    from unittest import TestSuite, makeSuite
    return TestSuite((makeSuite(TestReST),))
