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

"""Index Interface."""

from zope.interface import Interface

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
