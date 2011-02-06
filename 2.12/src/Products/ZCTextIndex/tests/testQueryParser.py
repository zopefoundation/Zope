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

from unittest import TestCase, TestSuite, main, makeSuite

class TestInterfaces(TestCase):

    def testInterfaces(self):
        from zope.interface.verify import verifyClass
        from Products.ZCTextIndex.IQueryParser import IQueryParser
        from Products.ZCTextIndex.QueryParser import QueryParser
        verifyClass(IQueryParser, QueryParser)


class TestQueryParserBase(TestCase):

    def setUp(self):
        from Products.ZCTextIndex.QueryParser import QueryParser
        from Products.ZCTextIndex.Lexicon import Lexicon
        from Products.ZCTextIndex.Lexicon import Splitter
        self.lexicon = Lexicon(Splitter())
        self.parser = QueryParser(self.lexicon)

    def expect(self, input, output, expected_ignored=[]):
        tree = self.parser.parseQuery(input)
        ignored = self.parser.getIgnored()
        self.compareParseTrees(tree, output)
        self.assertEqual(ignored, expected_ignored)
        # Check that parseQueryEx() == (parseQuery(), getIgnored())
        ex_tree, ex_ignored = self.parser.parseQueryEx(input)
        self.compareParseTrees(ex_tree, tree)
        self.assertEqual(ex_ignored, expected_ignored)

    def failure(self, input):
        from Products.ZCTextIndex.ParseTree import ParseError
        self.assertRaises(ParseError, self.parser.parseQuery, input)
        self.assertRaises(ParseError, self.parser.parseQueryEx, input)

    def compareParseTrees(self, got, expected, msg=None):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import GlobNode
        from Products.ZCTextIndex.ParseTree import NotNode
        from Products.ZCTextIndex.ParseTree import OrNode
        from Products.ZCTextIndex.ParseTree import ParseTreeNode
        from Products.ZCTextIndex.ParseTree import PhraseNode
        if msg is None:
            msg = repr(got)
        self.assertEqual(isinstance(got, ParseTreeNode), 1)
        self.assertEqual(got.__class__, expected.__class__, msg)
        if isinstance(got, PhraseNode):
            self.assertEqual(got.nodeType(), "PHRASE", msg)
            self.assertEqual(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, GlobNode):
            self.assertEqual(got.nodeType(), "GLOB", msg)
            self.assertEqual(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, AtomNode):
            self.assertEqual(got.nodeType(), "ATOM", msg)
            self.assertEqual(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, NotNode):
            self.assertEqual(got.nodeType(), "NOT")
            self.compareParseTrees(got.getValue(), expected.getValue(), msg)
        elif isinstance(got, AndNode) or isinstance(got, OrNode):
            self.assertEqual(got.nodeType(),
                             isinstance(got, AndNode) and "AND" or "OR", msg)
            list1 = got.getValue()
            list2 = expected.getValue()
            self.assertEqual(len(list1), len(list2), msg)
            for i in range(len(list1)):
                self.compareParseTrees(list1[i], list2[i], msg)


class TestQueryParser(TestQueryParserBase):

    def test001(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect("foo", AtomNode("foo"))

    def test002(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect("note", AtomNode("note"))

    def test003(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect("aa and bb AND cc",
                    AndNode([AtomNode("aa"), AtomNode("bb"), AtomNode("cc")]))

    def test004(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import OrNode
        self.expect("aa OR bb or cc",
                    OrNode([AtomNode("aa"), AtomNode("bb"), AtomNode("cc")]))

    def test005(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import OrNode
        self.expect("aa AND bb OR cc AnD dd",
                    OrNode([AndNode([AtomNode("aa"), AtomNode("bb")]),
                            AndNode([AtomNode("cc"), AtomNode("dd")])]))

    def test006(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import OrNode
        self.expect("(aa OR bb) AND (cc OR dd)",
                    AndNode([OrNode([AtomNode("aa"), AtomNode("bb")]),
                             OrNode([AtomNode("cc"), AtomNode("dd")])]))

    def test007(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import NotNode
        self.expect("aa AND NOT bb",
                    AndNode([AtomNode("aa"), NotNode(AtomNode("bb"))]))

    def test010(self):
        from Products.ZCTextIndex.ParseTree import PhraseNode
        self.expect('"foo bar"', PhraseNode(["foo", "bar"]))

    def test011(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect("foo bar", AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test012(self):
        from Products.ZCTextIndex.ParseTree import PhraseNode
        self.expect('(("foo bar"))"', PhraseNode(["foo", "bar"]))

    def test013(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect("((foo bar))", AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test014(self):
        from Products.ZCTextIndex.ParseTree import PhraseNode
        self.expect("foo-bar", PhraseNode(["foo", "bar"]))

    def test015(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import NotNode
        self.expect("foo -bar", AndNode([AtomNode("foo"),
                                         NotNode(AtomNode("bar"))]))

    def test016(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import NotNode
        self.expect("-foo bar", AndNode([AtomNode("bar"),
                                         NotNode(AtomNode("foo"))]))

    def test017(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import NotNode
        from Products.ZCTextIndex.ParseTree import PhraseNode
        self.expect("booh -foo-bar",
                    AndNode([AtomNode("booh"),
                             NotNode(PhraseNode(["foo", "bar"]))]))

    def test018(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import NotNode
        from Products.ZCTextIndex.ParseTree import PhraseNode
        self.expect('booh -"foo bar"',
                    AndNode([AtomNode("booh"),
                             NotNode(PhraseNode(["foo", "bar"]))]))

    def test019(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('foo"bar"',
                    AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test020(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('"foo"bar',
                    AndNode([AtomNode("foo"), AtomNode("bar")]))

    def test021(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('foo"bar"blech',
                    AndNode([AtomNode("foo"), AtomNode("bar"),
                             AtomNode("blech")]))

    def test022(self):
        from Products.ZCTextIndex.ParseTree import GlobNode
        self.expect("foo*", GlobNode("foo*"))

    def test023(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        from Products.ZCTextIndex.ParseTree import AtomNode
        from Products.ZCTextIndex.ParseTree import GlobNode
        self.expect("foo* bar", AndNode([GlobNode("foo*"),
                                         AtomNode("bar")]))

    def test101(self):
        self.failure("")

    def test102(self):
        self.failure("not")

    def test103(self):
        self.failure("or")

    def test104(self):
        self.failure("and")

    def test105(self):
        self.failure("NOT")

    def test106(self):
        self.failure("OR")

    def test107(self):
        self.failure("AND")

    def test108(self):
        self.failure("NOT foo")

    def test109(self):
        self.failure(")")

    def test110(self):
        self.failure("(")

    def test111(self):
        self.failure("foo OR")

    def test112(self):
        self.failure("foo AND")

    def test113(self):
        self.failure("OR foo")

    def test114(self):
        self.failure("AND foo")

    def test115(self):
        self.failure("(foo) bar")

    def test116(self):
        self.failure("(foo OR)")

    def test117(self):
        self.failure("(foo AND)")

    def test118(self):
        self.failure("(NOT foo)")

    def test119(self):
        self.failure("-foo")

    def test120(self):
        self.failure("-foo -bar")

    def test121(self):
        self.failure("foo OR -bar")

    def test122(self):
        self.failure("foo AND -bar")


class StopWordTestQueryParser(TestQueryParserBase):

    def setUp(self):
        from Products.ZCTextIndex.QueryParser import QueryParser
        from Products.ZCTextIndex.Lexicon import Lexicon
        from Products.ZCTextIndex.Lexicon import Splitter
        # Only 'stop' is a stopword (but 'and' is still an operator)
        self.lexicon = Lexicon(Splitter(), FakeStopWordRemover())
        self.parser = QueryParser(self.lexicon)

    def test201(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('and/', AtomNode("and"))

    def test202(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('foo AND stop', AtomNode("foo"), ["stop"])

    def test203(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('foo AND NOT stop', AtomNode("foo"), ["stop"])

    def test204(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('stop AND foo', AtomNode("foo"), ["stop"])

    def test205(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('foo OR stop', AtomNode("foo"), ["stop"])

    def test206(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self.expect('stop OR foo', AtomNode("foo"), ["stop"])

    def test301(self):
        self.failure('stop')

    def test302(self):
        self.failure('stop stop')

    def test303(self):
        self.failure('stop AND stop')

    def test304(self):
        self.failure('stop OR stop')

    def test305(self):
        self.failure('stop -foo')

    def test306(self):
        self.failure('stop AND NOT foo')


class FakeStopWordRemover:

    def process(self, list):
        return [word for word in list if word != "stop"]


def test_suite():
    return TestSuite((makeSuite(TestQueryParser),
                      makeSuite(StopWordTestQueryParser),
                      makeSuite(TestInterfaces),
                    ))


if __name__=="__main__":
    main(defaultTest='test_suite')
