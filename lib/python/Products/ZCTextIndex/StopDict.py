"""Provide a default list of stop words for the index.

The specific splitter and lexicon are customizable, but the default
ZCTextIndex should do something useful.
"""

def get_stopdict():
    """Return a dictionary of stopwords."""
    return _dict

# This list of English stopwords comes from Lucene
_words = [
    "a", "and", "are", "as", "at", "be", "but", "by",
    "for", "if", "in", "into", "is", "it",
    "no", "not", "of", "on", "or", "such",
    "that", "the", "their", "then", "there", "these",
    "they", "this", "to", "was", "will", "with"
]

_dict = {}
for w in _words:
    _dict[w] = None
