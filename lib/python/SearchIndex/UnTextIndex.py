##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""Text Index

The UnTextIndex falls under the 'I didnt have a better name for it'
excuse.  It is an 'Un' Text index because it stores a little bit of
undo information so that objects can be unindexed when the old value
is no longer known.
"""

__version__ = '$Revision: 1.35 $'[11:-2]


import BTree, IIBTree, IOBTree, OIBTree
import string, regex, regsub, ts_regex
import operator

from intSet import intSet
from Globals import Persistent
from Acquisition import Implicit
from Splitter import Splitter
from zLOG import LOG, ERROR
from Lexicon import Lexicon
from ResultList import ResultList
from types import *

BTree = BTree.BTree                     # Regular generic BTree
IOBTree = IOBTree.BTree                 # Integer -> Object 
IIBucket = IIBTree.Bucket               # Integer -> Integer
OIBTree = OIBTree.BTree                 # Object -> Integer

AndNot = 'andnot'
And = 'and'
Or = 'or'
Near = '...'
QueryError = 'TextIndex.QueryError'

            
class UnTextIndex(Persistent, Implicit):
    """Full-text index.

    There is a ZCatalog UML model that sheds some light on what is
    going on here.  '_index' is a BTree which maps word ids to mapping
    from document id to score.  Something like:

      {'bob' : {1 : 5, 2 : 3, 42 : 9}}
      {'uncle' : {1 : 1}}


    The '_unindex' attribute is a mapping from document id to word
    ids.  This mapping allows the catalog to unindex an object:

      {42 : ('bob', 'is', 'your', 'uncle')

    This isn't exactly how things are represented in memory, many
    optimizations happen along the way."""

    meta_type = 'Text Index'


    def __init__(self, id=None, ignore_ex=None,
                 call_methods=None, lexicon=None):
        """Create an index

        The arguments are:

          'id' -- the name of the item attribute to index.  This is
          either an attribute name or a record key.

          'ignore_ex' -- Tells the indexer to ignore exceptions that
          are rasied when indexing an object.

          'call_methods' -- Tells the indexer to call methods instead
          of getattr or getitem to get an attribute.

          'lexicon' is the lexicon object to specify, if None, the
          index will use a private lexicon."""
        
        if not id == ignore_ex == call_methods == None:
            self.id = id
            self.ignore_ex = ignore_ex
            self.call_methods = call_methods
            self._index = IOBTree()
            self._unindex = IOBTree()

        else:
            pass

        if lexicon is None:
            ## if no lexicon is provided, create a default one
            self._lexicon = Lexicon()
        else:
            self._lexicon = lexicon


    def getLexicon(self, vocab_id):
        """Return the Lexicon in use.
        
        Bit of a hack, indexes have been made acquirers so that they
        can acquire a vocabulary object from the object system in
        Zope.  I don't think indexes were ever intended to participate
        in this way, but I don't see too much of a problem with it."""

        if type(vocab_id) is not StringType:
            vocab = vocab_id
        else:
            vocab = getattr(self, vocab_id)
        return vocab.lexicon
        

    def __len__(self):
        """Return the number of objects indexed."""

        return len(self._unindex)


    def clear(self):
        """Reinitialize the text index."""
        
        self._index = IOBTree()
        self._unindex = IOBTree()


    def histogram(self):
        """Return a mapping which provides a histogram of the number of
        elements found at each point in the index."""

        histogram = {}
        for (key, value) in self._index.items():
            entry = len(value)
            histogram[entry] = histogram.get(entry, 0) + 1

        return histogram


    def getEntryForObject(self, rid, default=None):
        """Get all information contained for a specific object.

        This takes the objects record ID as it's main argument."""

        wordMap = self.getLexicon(self._lexicon)._lexicon.items()
        results = self._unindex.get(rid, None)

        if results is None:
            return default
        else:
            # Now that we've got them, let's resolve out the word
            # references
            resolved = []
            for (word, wordId) in wordMap:
                if wordId in results:
                    resolved.append(word)
            return tuple(resolved)
        
            
    def insertForwardIndexEntry(self, entry, documentId, score=1):
        """Uses the information provided to update the indexes.

        The basic logic for choice of data structure is based on
        the number of entries as follows:

            1      tuple
            2-4    dictionary
            5+     bucket.
        """

        indexRow = self._index.get(entry, None)

        if indexRow is not None:
            if type(indexRow) is TupleType:
                # Tuples are only used for rows which have only
                # a single entry.  Since we now need more, we'll
                # promote it to a mapping object (dictionary).

                # First, make sure we're not already in it, if so
                # update the score if necessary.
                if indexRow[0] == documentId:
                    if indexRow[1] != score:
                        indexRow = (documentId, score)
                else:
                    indexRow = { indexRow[0]: indexRow[1] }
                    indexRow[documentId] = score
                    self._index[entry] = indexRow
            elif type(indexRow) is DictType:
                if indexRow.has_key(documentId):
                    if indexRow[documentId] == score:
                        return 1    # No need to update
                elif len(indexRow) > 4:
                    # We have a mapping (dictionary), but it has
                    # grown too large, so we'll convert it to a
                    # bucket.
                    newRow = IIBucket()
                    for (k, v) in indexRow.items():
                        newRow[k] = v
                    indexRow = newRow
                    indexRow[documentId] = score
                    self._index[entry] = indexRow
                else:
                    indexRow[documentId] = score
            else:
                # We've got a IIBucket already.
                if indexRow.has_key(documentId):
                    if indexRow[documentId] == score:
                        return 1
                indexRow[documentId] = score
        else:
            # We don't have any information at this point, so we'll
            # put our first entry in, and use a tuple to save space
            self._index[entry] = (documentId, score)
        return 1


    def insertReverseIndexEntry(self, entry, documentId):
        """Insert the correct entry into the reverse indexes for future
        unindexing."""

        newRow = self._unindex.get(documentId, [])
        if newRow:
            # Catch cases where we don't need to modify anything
            if entry in newRow:
                return 1
        newRow.append(entry)
        self._unindex[documentId] = newRow


    def removeReverseEntry(self, entry, documentId):
        """Removes a single entry from the reverse index."""

        newRow = self._unindex.get(documentId, [])
        if newRow:
            try:
                newRow.remove(entry)
            except ValueError:
                pass                    # We don't have it, this is bad
        self._unindex[documentId] = newRow


    def removeForwardEntry(self, entry, documentId):
        """Remove a single entry from the forward index."""

        currentRow = self._index.get(entry, None)
        if type(currentRow) is TupleType:
            del self._index[entry]
        elif currentRow is not None:
            try:
                del self._index[entry][documentId]
            except (KeyError, IndexError, TypeError):
                LOG('UnTextIndex', ERROR,
                    'unindex_object tried to unindex nonexistent'
                    ' document %s' % str(i))

    def index_object(self, documentId, obj, threshold=None):
        """ Index an object:
        'documentId' is the integer id of the document
        
        'obj' is the objects to be indexed

        'threshold' is the number of words to process between
        commiting subtransactions.  If 'None' subtransactions are
        disabled. """

        # sniff the object for our 'id', the 'document source' of the
        # index is this attribute.  If it smells callable, call it.
        try:
            source = getattr(obj, self.id)
            if callable(source):
                source = str(source())
            else:
                source = str(source)
        except AttributeError:
            return 0
        

        sourceWords = self.getLexicon(self._lexicon).Splitter(source)

        wordList = OIBTree()
        last = None
        
        # Run through the words and score them
        for word in sourceWords:
            if word[0] == '\"':
                last = self.subindex(word[1:-1], wordList,
                                     wordList.has_key, last) # XXX
            else:
                if wordList.has_key(word):
                    if word != last:
                        wordList[word] = wordList[word]+1
                else:
                    wordList[word] = 1

        lexicon = self.getLexicon(self._lexicon)
        currentWordIds = self._unindex.get(documentId, [])
        wordCount = 0

        # First deal with deleted words
        # To do this, the first thing we have to do is convert the
        # existing words to words, from wordIDS
        wordListAsIds = OIBTree()
        for word, score in wordList.items():
            wordListAsIds[lexicon.getWordId(word)] = score
        
        for word in currentWordIds:
            if not wordListAsIds.has_key(word):
                self.removeForwardEntry(word, documentId)

        #import pdb; pdb.set_trace()
        # Now we can deal with new/updated entries
        for wordId, score in wordListAsIds.items():
            self.insertForwardIndexEntry(wordId, documentId, score)
            self.insertReverseIndexEntry(wordId, documentId)
            wordCount = wordCount + 1

        # Return the number of words you indexed
        return wordCount


    def unindex_object(self, i): 
        """ carefully unindex document with integer id 'i' from the text
        index and do not fail if it does not exist """

        index = self._index
        unindex = self._unindex
        val = unindex.get(i, None)
        if val is not None:
            for n in val:
                v = index.get(n, None)
                if type(v) is TupleType:
                    del index[n]
                elif v is not None:
                    try:
                        del index[n][i]
                    except (KeyError, IndexError, TypeError):
                        LOG('UnTextIndex', ERROR,
                            'unindex_object tried to unindex nonexistent'
                            ' document %s' % str(i))
            del unindex[i]


    def __getitem__(self, word):
        """Return an InvertedIndex-style result "list"

        Note that this differentiates between being passed an Integer
        and a String.  Strings are looked up in the lexicon, whereas
        Integers are assumed to be resolved word ids. """
        
        if type(word) is IntType:
            # We have a word ID
            result = self._index.get(word, {})
            return ResultList(result, (word,), self)
        else:
            splitSource = tuple(self.getLexicon(self._lexicon).Splitter(word))

            if not splitSource:
                return ResultList({}, (word,), self)
        
            if len(splitSource) == 1:
                splitSource = splitSource[0]
                if splitSource[:1] == '"' and splitSource[-1:] == '"':
                    return self[splitSource]

                r = self._index.get(
                     self.getLexicon(self._lexicon).get(splitSource)[0],
                     None)

                if r is None:
                    r = {}

                return ResultList(r, (splitSource,), self)

            r = None
            for word in splitSource:
                rr = self[word]
                if r is None:
                    r = rr
                else:
                    r = r.near(rr)

            return r


    def _apply_index(self, request, cid=''): 
        """ Apply the index to query parameters given in the argument,
        request

        The argument should be a mapping object.

        If the request does not contain the needed parameters, then
        None is returned.
 
        Otherwise two objects are returned.  The first object is a
        ResultSet containing the record numbers of the matching
        records.  The second object is a tuple containing the names of
        all data fields used.  
        """

        if request.has_key(self.id):
            keys = request[self.id]
        else:
            return None

        if type(keys) is StringType:
            if not keys or not string.strip(keys):
                return None
            keys = [keys]
        r = None
        
        for key in keys:
            key = string.strip(key)
            if not key:
                continue
            
            rr = IIBucket()
            try:
                 for i, score in self.query(key).items():
                    if score:
                        rr[i] = score
            except KeyError:
                pass
            if r is None:
                r = rr
            else:
                # Note that we *and*/*narrow* multiple search terms.
                r = r.intersection(rr) 

        if r is not None:
            return r, (self.id,)
        return (IIBucket(), (self.id,))


    def positions(self, docid, words, obj):
        """Return the positions in the document for the given document
        id of the word, word."""

        if self._schema is None:
            f = getattr
        else:
            f = operator.__getitem__
            id = self._schema[self.id]


        if self.call_methods:
            doc = str(f(obj, self.id)())
        else:
            doc = str(f(obj, self.id))

        r = []
        for word in words:
            r = r+self.getLexicon(self._lexicon).Splitter(doc).indexes(word)
        return r


    def _subindex(self, isrc, d, old, last):
        src = self.getLexicon(self._lexicon).Splitter(isrc)  

        for s in src:
            if s[0] == '\"':
                last = self.subindex(s[1:-1],d,old,last)
            else:
                if old(s):
                    if s != last: d[s] = d[s]+1
                else: d[s] = 1

        return last


    def query(self, s, default_operator=Or, ws=(string.whitespace,)):
        """ This is called by TextIndexes.  A 'query term' which is a
        string 's' is passed in, along with an index object.  s is
        parsed, then the wildcards are parsed, then something is
        parsed again, then the whole thing is 'evaluated'. """

        # First replace any occurences of " and not " with " andnot "
        s = ts_regex.gsub(
            '[%s]+[aA][nN][dD][%s]*[nN][oO][tT][%s]+' % (ws * 3),
            ' andnot ', s)

        # do some parsing
        q = parse(s)

        ## here, we give lexicons a chance to transform the query.
        ## For example, substitute wildcards, or translate words into
        ## various languages.
        q = self.getLexicon(self._lexicon).query_hook(q)
        
        # do some more parsing
        q = parse2(q, default_operator)

        ## evalute the final 'expression'
        return self.evaluate(q)


    def get_operands(self, q, i):
        """Evaluate and return the left and right operands for an operator"""
        
        try:
            left  = q[i - 1]
            right = q[i + 1]
        except IndexError:
            raise QueryError, "Malformed query"

        operandType = type(left)
        if operandType is IntType:
            left = self[left]
        elif operandType is StringType:
            left = self[left]        
        elif operandType is ListType:
            left = evaluate(left, self)

        operandType = type(right)
        if operandType is IntType:
            right = self[right]
        elif operandType is StringType:
            right = self[right]       
        elif operandType is ListType:
            right = evaluate(right, self)

        return (left, right)


    def evaluate(self, query):
        """Evaluate a parsed query"""
        # There are two options if the query passed in is only one
        # item. It means either it's an embedded query, in which case
        # we'll recursively evaluate, other wise it's nothing for us
        # to evaluate, and we just get the results and return them.
        if (len(query) == 1):
            if (type(query[0]) is ListType):
                return evaluate(query[0], self)

            return self[query[0]]       # __getitem__

        # Now we need to loop through the query and expand out
        # operators.  They are currently evaluated in the following
        # order: AndNote -> And -> Or -> Near
        i = 0
        while (i < len(query)):
            if query[i] is AndNot:
                left, right = self.get_operands(query, i)
                val = left.and_not(right)
                query[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        i = 0
        while (i < len(query)):
            if query[i] is And:
                left, right = self.get_operands(query, i)
                val = left & right
                query[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        i = 0
        while (i < len(query)):
            if query[i] is Or:
                left, right = self.get_operands(query, i)
                val = left | right
                query[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        i = 0
        while (i < len(query)):
            if query[i] is Near:
                left, right = self.get_operands(query, i)
                val = left.near(right)
                query[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        if (len(query) != 1): raise QueryError, "Malformed query"

        return query[0]


def parse(s):
    """Parse parentheses and quotes"""
    l = []
    tmp = string.lower(s)

    while (1):
        p = parens(tmp)

        if (p is None):
            # No parentheses found.  Look for quotes then exit.
            l = l + quotes(tmp)
            break
        else:
            # Look for quotes in the section of the string before
            # the parentheses, then parse the string inside the parens
            l = l + quotes(tmp[:(p[0] - 1)])
            l.append(parse(tmp[p[0] : p[1]]))

            # continue looking through the rest of the string
            tmp = tmp[(p[1] + 1):]

    return l

def parse2(q, default_operator,
           operator_dict={AndNot: AndNot, And: And, Or: Or, Near: Near}):
    """Find operators and operands"""
    i = 0
    isop = operator_dict.has_key
    while (i < len(q)):
        if (type(q[i]) is ListType): q[i] = parse2(q[i], default_operator)

        # every other item, starting with the first, should be an operand
        if ((i % 2) != 0):
            # This word should be an operator; if it is not, splice in
            # the default operator.
            
            if type(q[i]) is not ListType and isop(q[i]):
                q[i] = operator_dict[q[i]]
            else: q[i : i] = [ default_operator ]

        i = i + 1

    return q


def parens(s, parens_re=regex.compile('(\|)').search):

    index = open_index = paren_count = 0

    while 1:
        index = parens_re(s, index)
        if index < 0 : break
    
        if s[index] == '(':
            paren_count = paren_count + 1
            if open_index == 0 : open_index = index + 1
        else:
            paren_count = paren_count - 1

        if paren_count == 0:
            return open_index, index
        else:
            index = index + 1

    if paren_count == 0: # No parentheses Found
        return None
    else:
        raise QueryError, "Mismatched parentheses"      



def quotes(s, ws=(string.whitespace,)):
     # split up quoted regions
     splitted = ts_regex.split(s, '[%s]*\"[%s]*' % (ws * 2))
     split=string.split

     if (len(splitted) > 1):
         if ((len(splitted) % 2) == 0): raise QueryError, "Mismatched quotes"
    
         for i in range(1,len(splitted),2):
             # split the quoted region into words
             splitted[i] = filter(None, split(splitted[i]))

             # put the Proxmity operator in between quoted words
             for j in range(1, len(splitted[i])):
                 splitted[i][j : j] = [ Near ]

         for i in range(len(splitted)-1,-1,-2):
             # split the non-quoted region into words
             splitted[i:i+1] = filter(None, split(splitted[i]))

         splitted = filter(None, splitted)
     else:
         # No quotes, so just split the string into words
         splitted = filter(None, split(s))

     return splitted
