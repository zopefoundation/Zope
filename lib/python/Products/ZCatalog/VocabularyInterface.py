from Zope.Interfaces.Interface import Interface

from OFS.ItemInterface import ItemInterface
class Vocabulary:
    """

    Vocabulary objects encapsulate language dependent features for
    text indexing.  This is mostly used by the ZCatalog, but other
    objects that require language dependent features may use
    Vocabulary objects.

    The main task of a Vocabulary object is to maintain a mapping from 
    integers (called 'word ids') to 'words'.  In this sense, 'words'
    can be any string of characters in any language.  To understand
    why this is useful, a little background on text indexing will be given.

    In general, text indexes maintain a mapping from words to a list
    of 'objects' that contain that word.  This is just like the index
    in the back of a book, which maintains a mapping from a word to a
    list of pages in the book where that word occurs.  In the case of
    a book, the 'objects' are pages in the book.  An index typically
    looks like this::

      foo ->  (1, 5, 13, 66)
      bar ->  (5, 42)

    Here, 'foo' and 'bar' are mapped to lists of 'objects' (or pages,
    or whatever), that contain them.

    The ZCatalog's text indexes in Zope work almost identically, but
    instead of mapping a *word* to a list of objects, it maps a *word
    id*.  This word id is an integer.

    Vocabulary objects maintain this mapping from word to word id.
    Because they are seperated out into a different object, ZCatalogs
    can work with a variety of Vocabulary objects that implement this
    interface.  This means that the ZCatalog is entirely language
    neutral, and supporting other languages, and their possibly wildly 
    different concept of 'word', is mearly an excercise in creating a
    new kind of Vocabulary object; there is no need to rewrite
    something as complex as the ZCatalog to support new languages.

    """

    __extends__ = (ItemInterface,)

    def query(self, pattern):
        """

        Returns a sequence of integer word ids for words that match
        'pattern'.  Vocabulary objects many interpret this pattern in
        any way.  For example, the current implementation of Zope's
        vocabulary object's can be either globbing or non-globbing.
        Non-globbing vocabularies do not interpret 'pattern' in any
        special way and will allways return a sequence of 1 or less
        integers.  Globbing Vocabulary objects understand a minimal
        set of 'globbing' wildcard characters that are be default '*'
        and '?'.  Globbing lexicons will return a sequence of zero or
        more word ids for words that match the globbing 'pattern'.

        """
        
    def insert(self, word=''):
        """

        Inserts 'word' into the Vocabulary mapping and assigns it a
        new word id.  This method returns nothing.

        """

    def words(self):
        """

        Returns a sequence of all words in the Vocabulary.

        """


VocabularyInterface=Interface(Vocabulary) # create the interface object










