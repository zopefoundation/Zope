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

Notes on a new text index design

  The current inverted index algoirthm works well enough for our needs.
  Speed of the algorithm does not seem to be a problem, however, data
  management *is* a significant problem.  In particular:

    - Process size grows unacceptably *during mass indexing*.

    - Data load and store seems to take too long.  For example,
      clearing an inverted index and committing takes a significant
      amount of time.

    - The current trie data structure contributes significantly to the
      number of objects in the system.

    - Removal/update of documents is especially problematic.  We have
      to either:

      - Unindex old version of an object before updating it.  This is
        a real hassle for apps like sws.

      - Tool through entire index looking for object references.  This
        is *totally* impractical.

  Some observations of competition:

    - Xerox system can index "5-million word document in 256k".  What
      does this mean?

        - Does the system save word positions as we do?

        - What is the index indexing?

        - What was the vocabulary of the system?

      Let\'s see.  Assume a 10,000 word vocabulary.  Then we use
      25-bytes per entry.  Hm.....

    - Verity has some sense of indexing in phases and packing index.
      Verity keeps the index in multiple chunks and a search may
      operate on multiple chunks.  This means that we can add data
      without updating large records.

      This may be especially handy for mass updates, like we do in
      cv3.  In a sense we do this in cv3 and sws.  We index a large
      batch of documents to a temporary index and then merge changes
      in.

      If "temporary" index was integral to system, then maybe merger
      could be done as a background task....

  Tree issues

    Tree structures benefit small updates, because an update to an
    entry does not cause update of entire tree, however, each node in
    tree introduces overhead.

    Trie structure currently introduces an excessive number of nodes.
    Typically, a node per two or three words.  Trie has potential to 
    reduce storage because key storage is shared between words.

    Maybe an alternative to a Trie is some sort of nested BTree.  Or
    maybe a Trie with some kind of binary-search-based indexing.

    Suppose that:

      - database objects were at leaves of tree
      - vocabulary was finite
      - we don\'t remove a leaf when it becomes empty

    Then:

      - After some point, tree objects no longer change
    
    If this is case, then it doesn\'t make sense to optimize tree for
    change. 

  Additional notes

    Stemming reduces the number of words substantially.

  Proposal -- new TextIndex

    TextIndex -- word -> textSearchResult

      Implemented with:

        InvertedIndex -- word -> idSet

        ResultIndex -- id -> docData

        where:

          word -- is a token, typically a word, but could be a name or a
                  number

          textSearchResult -- id -> (score, positions)

          id -- integer, say 4-byte.
          
          positions -- sequence of integers.

          score -- numeric measure of relevence, f(numberOfWords, positions)

          numberOfWords -- number of words in source document.

          idSet -- set of ids

          docData -- numberOfWords, word->positions

       Note that ids and positions are ints.  We will build C
       extensions for efficiently storing and pickling structures
       with lots of ints.  This should significantly improve space
       overhead and storage/retrieveal times, as well as storeage
       space.

"""
__version__='$Revision: 1.24 $'[11:-2]

from Globals import Persistent
import BTree, IIBTree
BTree=BTree.BTree
IIBTree=IIBTree.Bucket
from intSet import intSet
import operator
from Splitter import Splitter
from string import strip
import string, ts_regex, regex

from Lexicon import *
from ResultList import ResultList

class TextIndex(Persistent):

    def __init__(self, data=None, schema=None, id=None,
                 ignore_ex=None, call_methods=None):
        """Create an index

        The arguments are:

          'data' -- a mapping from integer object ids to objects or
          records,

          'schema' -- a mapping from item name to index into data
          records.  If 'data' is a mapping to objects, then schema
          should ne 'None'.

          'id' -- the name of the item attribute to index.  This is
          either an attribute name or a record key.

          'ignore_ex' -- Tells the indexer to ignore exceptions that
          are rasied when indexing an object.

          'call_methods' -- Tells the indexer to call methods instead
          of getattr or getitem to get an attribute.

        """
        ######################################################################
        # For b/w compatability, have to allow __init__ calls with zero args
        if not data==schema==id==ignore_ex==call_methods==None:
            self._data=data
            self._schema=schema
            self.id=id
            self.ignore_ex=ignore_ex
            self.call_methods=call_methods
            self._index=BTree()
            self._syn=stop_word_dict
            self._reindex()
        else:
            pass

    # for backwards compatability
    _init = __init__


    def clear(self):
        self._index = BTree()


    def positions(self, docid, words):
        """Return the positions in the document for the given document
        id of the word, word."""
        id = self.id

        if self._schema is None:
            f = getattr
        else:
            f = operator.__getitem__
            id = self._schema[id]


        row = self._data[docid]

        if self.call_methods:
            doc = str(f(row, id)())
        else:
            doc = str(f(row, id))

        r = []
        for word in words:
            r = r+Splitter(doc, self._syn).indexes(word)
        return r


    def index_item(self, i, obj=None, un=0):
        """Recompute index data for data with ids >= start.
        if 'obj' is passed in, it is indexed instead of _data[i]"""

        id = self.id
        if (self._schema is None) or (obj is not None):
            f = getattr
        else:
            f = operator.__getitem__
            id = self._schema[id]

        if obj is None:
            obj = self._data[i]

        try:
            if self.call_methods:
                k = str(f(obj, id)())
            else:
                k = str(f(obj, id))

            self._index_document(k, i ,un)
        except:
            pass


    def unindex_item(self, i, obj=None): 
        return self.index_item(i, obj, 1)


    def _reindex(self, start=0):
        """Recompute index data for data with ids >= start."""
        for i in self._data.keys(start): self.index_item(i)


    def _index_document(self, document_text, id, un=0,
                        tupleType=type(()),
                        dictType=type({}),
                        ):
        src = Splitter(document_text, self._syn)  

        d = {}
        old = d.has_key
        last = None
        
        for s in src:
            if s[0] == '\"': last=self.subindex(s[1:-1], d, old, last)
            else:
                if old(s):
                    if s != last: d[s] = d[s]+1
                else: d[s] = 1

        index = self._index
        get = index.get
        if un:
            for word,score in d.items():
                r = get(word)
                if r is not None:
                    if type(r) is tupleType: del index[word]
                    else:
                        if r.has_key(id): del r[id]
                        if type(r) is dictType:
                            if len(r) < 2:
                                if r:
                                    for k, v in r.items(): index[word] = k,v
                                else: del index[word]
                            else: index[word] = r
        else:
            for word,score in d.items():
                r = get(word)
                if r is not None:
                    r = index[word]
                    if type(r) is tupleType:
                        r = {r[0]:r[1]}
                        r[id] = score
                        index[word] = r
                    elif type(r) is dictType:
                        if len(r) > 4:
                            b = IIBTree()
                            for k, v in r.items(): b[k] = v
                            r = b
                        r[id] = score
                        index[word] = r
                    else: r[id] = score
                else: index[word] = id, score


    def _subindex(self, isrc, d, old, last):

        src = Splitter(isrc, self._syn)  

        for s in src:
            if s[0] == '\"': last=self.subindex(s[1:-1],d,old,last)
            else:
                if old(s):
                    if s != last: d[s] = d[s]+1
                else: d[s] = 1

        return last


    def __getitem__(self, word):
        """Return an InvertedIndex-style result "list"
        """
        src = tuple(Splitter(word, self._syn))
        if not src: return ResultList({}, (word,), self)
        if len(src) == 1:
            src=src[0]
            if src[:1]=='"' and src[-1:]=='"': return self[src]
            r = self._index.get(word,None)
            if r is None: r = {}
            return ResultList(r, (word,), self)
            
        r = None
        for word in src:
            rr = self[word]
            if r is None: r = rr
            else: r = r.near(rr)

        return r


    def _apply_index(self, request, cid='', ListType=[]): 
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

        id = self.id

        cidid = "%s/%s" % (cid, id)
        has_key = request.has_key
        if has_key(cidid): keys = request[cidid]
        elif has_key(id): keys =request[id]
        else: return None

        if type(keys) is type(''):
            if not keys or not strip(keys): return None
            keys = [keys]
        r = None
        for key in keys:
            key = strip(key)
            if not key: continue
            rr = intSet()
            try:
                for i,score in query(key,self).items():
                    if score: rr.insert(i)
            except KeyError: pass
            if r is None: r = rr
            else:
                # Note that we *and*/*narrow* multiple search terms.
                r = r.intersection(rr) 

        if r is not None: return r, (id,)
        return intSet(), (id,)

