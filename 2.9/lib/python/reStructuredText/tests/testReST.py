
import unittest


class TestReST(unittest.TestCase):

    def testRoman(self):
        # Make sure we can import the rst parser
        from docutils.parsers import rst


def test_suite():
    from unittest import TestSuite, makeSuite
    return TestSuite((makeSuite(TestReST),))

