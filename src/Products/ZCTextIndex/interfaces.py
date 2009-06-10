##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZCTextIndex z3 interfaces.

$Id$
"""

from zope.interface import Interface


class IZCTextIndex(Interface):

    """Persistent text index.
    """


class ILexicon(Interface):

    """Object responsible for converting text to word identifiers.
    """

    def termToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parse the text as if they are search terms, and skips words
        that aren't in the lexicon.
        """

    def sourceToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parse the text as if they come from a source document, and
        creates new word ids for words that aren't (yet) in the
        lexicon.
        """

    def globToWordIds(pattern):
        """Return a sequence of ids of words matching the pattern.

        The argument should be a single word using globbing syntax,
        e.g. 'foo*' meaning anything starting with 'foo'.

        Return the wids for all words in the lexicon that match the
        pattern.
        """

    def length():
        """Return the number of unique term in the lexicon.
        """

    def get_word(wid):
        """Return the word for the given word id.

        Raise KeyError if the word id is not in the lexicon.
        """

    def get_wid(word):
        """Return the wird id for the given word.

        Return 0 of the word is not in the lexicon.
        """

    def parseTerms(text):
        """Pass the text through the pipeline.

        Return a list of words, normalized by the pipeline
        (e.g. stopwords removed, case normalized etc.).
        """

    def isGlob(word):
        """Return true if the word is a globbing pattern.

        The word should be one of the words returned by parseTerm().
        """


class IZCLexicon(Interface):

    """Lexicon for ZCTextIndex.
    """

class ISplitter(Interface):
    """A splitter."""

    def process(text):
        """Run the splitter over the input text, returning a list of terms.
        """

class IPipelineElement(Interface):

    def process(source):
        """Provide a text processing step.

        Process a source sequence of words into a result sequence.
        """

    def processGlob(source):
        """Process, passing through globbing metacharaters.

        This is an optional method; if it is not used, process() is used.
        """

class IPipelineElementFactory(Interface):
    """Class for creating pipeline elements by name"""

    def registerFactory(group, name, factory):
        """Registers a pipeline factory by name and element group.

        Each name can be registered only once for a given group. Duplicate
        registrations will raise a ValueError
        """

    def getFactoryGroups():
        """Returns a sorted list of element group names
        """

    def getFactoryNames(group):
        """Returns a sorted list of registered pipeline factory names
        in the specified element group
        """

    def instantiate(group, name):
        """Instantiates a pipeline element by group and name. If name is not
        registered raise a KeyError.
        """


class IQueryParseTree(Interface):
    """Interface for parse trees returned by parseQuery()."""

    def nodeType():
        """Return the node type.

        This is one of 'AND', 'OR', 'NOT', 'ATOM', 'PHRASE' or 'GLOB'.
        """

    def getValue():
        """Return a node-type specific value.

        For node type:    Return:
        'AND'             a list of parse trees
        'OR'              a list of parse trees
        'NOT'             a parse tree
        'ATOM'            a string (representing a single search term)
        'PHRASE'          a string (representing a search phrase)
        'GLOB'            a string (representing a pattern, e.g. "foo*")
        """

    def terms():
        """Return a list of all terms in this node, excluding NOT subtrees."""

    def executeQuery(index):
        """Execute the query represented by this node against the index.

        The index argument must implement the IIndex interface.

        Return an IIBucket or IIBTree mapping document ids to scores
        (higher scores mean better results).

        May raise ParseTree.QueryError.
        """

class IQueryParser(Interface):
    """Interface for Query Parsers."""

    def parseQuery(query):
        """Parse a query string.

        Return a parse tree (which implements IQueryParseTree).

        Some of the query terms may be ignored because they are
        stopwords; use getIgnored() to find out which terms were
        ignored.  But if the entire query consists only of stop words,
        or of stopwords and one or more negated terms, an exception is
        raised.

        May raise ParseTree.ParseError.
        """

    def getIgnored():
        """Return the list of ignored terms.

        Return the list of terms that were ignored by the most recent
        call to parseQuery() because they were stopwords.

        If parseQuery() was never called this returns None.
        """

    def parseQueryEx(query):
        """Parse a query string.

        Return a tuple (tree, ignored) where 'tree' is the parse tree
        as returned by parseQuery(), and 'ignored' is a list of
        ignored terms as returned by getIgnored().

        May raise ParseTree.ParseError.
        """

class IIndex(Interface):
    """Interface for an Index."""

    def length():
        """Return the number of words in the index."""
        
    def document_count():
        """Return the number of documents in the index."""

    def get_words(docid):
        """Return a list of wordids for the given docid."""

    def search(term):
        """Execute a search on a single term given as a string.

        Return an IIBTree mapping docid to score, or None if all docs
        match due to the lexicon returning no wids for the term (e.g.,
        if the term is entirely composed of stopwords).
        """

    def search_phrase(phrase):
        """Execute a search on a phrase given as a string.

        Return an IIBtree mapping docid to score.
        """

    def search_glob(pattern):
        """Execute a pattern search.

        The pattern represents a set of words by using * and ?.  For
        example, "foo*" represents the set of all words in the lexicon
        starting with "foo".

        Return an IIBTree mapping docid to score.
        """

    def query_weight(terms):
        """Return the weight for a set of query terms.

        'terms' is a sequence of all terms included in the query,
        although not terms with a not.  If a term appears more than
        once in a query, it should appear more than once in terms.

        Nothing is defined about what "weight" means, beyond that the
        result is an upper bound on document scores returned for the
        query.
        """

    def index_doc(docid, text):
        """Add a document with the specified id and text to the index. If a
        document by that id already exists, replace its text with the new
        text provided
        text  may be either a string (Unicode or otherwise) or a list
        of strings from which to extract the terms under which to
        index the source document.
        """

    def unindex_doc(docid):
        """Remove the document with the specified id from the index"""

    def has_doc(docid):
        """Returns true if docid is an id of a document in the index"""

class INBest(Interface):
    """NBest chooser Interface.

    An NBest object remembers the N best-scoring items ever passed to its
    .add(item, score) method.  If .add() is called M times, the worst-case
    number of comparisons performed overall is M * log2(N).
    """

    def add(item, score):
        """Record that item 'item' has score 'score'.  No return value.

        The N best-scoring items are remembered, where N was passed to
        the constructor.  'item' can by anything.  'score' should be
        a number, and larger numbers are considered better.
        """

    def addmany(sequence):
        """Like "for item, score in sequence: self.add(item, score)".

        This is simply faster than calling add() len(seq) times.
        """

    def getbest():
        """Return the (at most) N best-scoring items as a sequence.

        The return value is a sequence of 2-tuples, (item, score), with
        the largest score first.  If .add() has been called fewer than
        N times, this sequence will contain fewer than N pairs.
        """

    def pop_smallest():
        """Return and remove the (item, score) pair with lowest score.

        If len(self) is 0, raise IndexError.

        To be cleaer, this is the lowest score among the N best-scoring
        seen so far.  This is most useful if the capacity of the NBest
        object is never exceeded, in which case  pop_smallest() allows
        using the object as an ordinary smallest-in-first-out priority
        queue.
        """

    def __len__():
        """Return the number of (item, score) pairs currently known.

        This is N (the value passed to the constructor), unless .add()
        has been called fewer than N times.
        """

    def capacity():
        """Return the maximum number of (item, score) pairs.

        This is N (the value passed to the constructor).
        """
