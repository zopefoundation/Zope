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

"""Query Parser.

This particular parser recognizes the following syntax:

Start = OrExpr
OrExpr = AndExpr ('OR' AndExpr)*
AndExpr = Term ('AND' NotExpr)*
NotExpr = ['NOT'] Term
Term = '(' OrExpr ')' | ATOM+

The key words (AND, OR, NOT) are recognized in any mixture of case.

An ATOM is either:

+ A sequence of characters not containing whitespace or parentheses or
  double quotes, and not equal to one of the key words 'AND', 'OR', 'NOT'; or

+ A non-empty string enclosed in double quotes.  The interior of the string
  can contain whitespace, parentheses and key words.

In addition, an ATOM may optionally be preceded by a hyphen, meaning
that it must not be present.

An unquoted ATOM may also end in a star.  This is a primitive
"globbing" function, meaning to search for any word with a given
prefix.

When multiple consecutive ATOMs are found at the leaf level, they are
connected by an implied AND operator, and an unquoted leading hyphen
is interpreted as a NOT operator.

Summarizing the default operator rules:

- a sequence of words without operators implies AND, e.g. ``foo bar''
- double-quoted text implies phrase search, e.g. ``"foo bar"''
- words connected by punctuation implies phrase search, e.g. ``foo-bar''
- a leading hyphen implies NOT, e.g. ``foo -bar''
- these can be combined, e.g. ``foo -"foo bar"'' or ``foo -foo-bar''
- a trailing * means globbing (i.e. prefix search), e.g. ``foo*''
"""

import re

import ParseTree # relative import

# Create unique symbols for token types.
_AND    = intern("AND")
_OR     = intern("OR")
_NOT    = intern("NOT")
_LPAREN = intern("(")
_RPAREN = intern(")")
_ATOM   = intern("ATOM")
_EOF    = intern("EOF")

# Map keyword string to token type.
_keywords = {
    _AND:       _AND,
    _OR:        _OR,
    _NOT:       _NOT,
    _LPAREN:    _LPAREN,
    _RPAREN:    _RPAREN,
}

# Regular expression to tokenize.
_tokenizer_regex = re.compile(r"""
    # a paren
    [()]
    # or an optional hyphen
|   -?
    # followed by
    (?:
        # a string
        " [^"]* "
        # or a non-empty stretch w/o whitespace, parens or double quotes
    |    [^()\s"]+
    )
""", re.VERBOSE)

class QueryParser:

    def __init__(self, lexicon):
        self._lexicon = lexicon

    def parseQuery(self, query):
        # Lexical analysis.
        tokens = _tokenizer_regex.findall(query)
        self.__tokens = tokens
        # classify tokens
        self.__tokentypes = [_keywords.get(token.upper(), _ATOM)
                             for token in tokens]
        # add _EOF
        self.__tokens.append(_EOF)
        self.__tokentypes.append(_EOF)
        self.__index = 0

        # Syntactical analysis.
        tree = self._parseOrExpr()
        self._require(_EOF)
        return tree

    # Recursive descent parser

    def _require(self, tokentype):
        if not self._check(tokentype):
            t = self.__tokens[self.__index]
            msg = "Token %r required, %r found" % (tokentype, t)
            raise ParseTree.ParseError, msg

    def _check(self, tokentype):
        if self.__tokentypes[self.__index] is tokentype:
            self.__index += 1
            return 1
        else:
            return 0

    def _peek(self, tokentype):
        return self.__tokentypes[self.__index] is tokentype

    def _get(self, tokentype):
        t = self.__tokens[self.__index]
        self._require(tokentype)
        return t

    def _parseOrExpr(self):
        L = []
        L.append(self._parseAndExpr())
        while self._check(_OR):
            L.append(self._parseAndExpr())
        if len(L) == 1:
            return L[0]
        else:
            return ParseTree.OrNode(L)

    def _parseAndExpr(self):
        L = []
        L.append(self._parseTerm())
        while self._check(_AND):
            L.append(self._parseNotExpr())
        if len(L) == 1:
            return L[0]
        else:
            return ParseTree.AndNode(L)

    def _parseNotExpr(self):
        if self._check(_NOT):
            return ParseTree.NotNode(self._parseTerm())
        else:
            return self._parseTerm()

    def _parseTerm(self):
        if self._check(_LPAREN):
            tree = self._parseOrExpr()
            self._require(_RPAREN)
        else:
            atoms = [self._get(_ATOM)]
            while self._peek(_ATOM):
                atoms.append(self._get(_ATOM))
            nodes = []
            nots = []
            for a in atoms:
                words = re.findall(r"\w+\*?", a)
                if not words:
                    continue
                if len(words) > 1:
                    n = ParseTree.PhraseNode(" ".join(words))
                elif words[0].endswith("*"):
                    n = ParseTree.GlobNode(words[0])
                else:
                    n = ParseTree.AtomNode(words[0])
                if a[0] == "-":
                    n = ParseTree.NotNode(n)
                    nots.append(n)
                else:
                    nodes.append(n)
            if not nodes:
                text = " ".join(atoms)
                msg = "At least one positive term required: %r" % text
                raise ParseTree.ParseError, msg
            nodes.extend(nots)
            if len(nodes) == 1:
                tree = nodes[0]
            else:
                tree = ParseTree.AndNode(nodes)
        return tree
