############################################################################## 
#
#     Copyright 
#
#       Copyright 1997 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''Text Index

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



$Id: TextIndex.py,v 1.3 1997/09/17 17:53:32 jim Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

from Globals import Persistent
from Trie import Trie
from IOBTree import BTree
from intSet import intSet
from InvertedIndexQuery import query
from InvertedIndex import ResultList
import operator
getitem=operator.__getitem__
from WordSequence import WordSequence
from string import strip

class TextIndex(Persistent):

    def _init(self,data,schema,id):
	"""Create an index

	The arguments are:

	  'data' -- a mapping from integer object ids to objects or records,

	  'schema' -- a mapping from item name to index into data records.
              If 'data' is a mapping to objects, then schema should ne 'None'.

	  'id' -- the name of the item attribute to index.  This is either
	      an attribute name or a record key.
	"""
	self._data=data
	self._schema=schema
	self.id=id
	self._id2info=BTree()
	self._w2ids=Trie()
	self._syn={}
	
	self._reindex()

    def clear(self):
	self._init()
  

    def index_item(self,i):
	"""Recompute index data for data with ids >= start."""

	id=self.id
	if self._schema is None:
	    f=getattr
	else:
	    f=getitem
	    id=self._schema[id]

	row=self._data[i]
	k=f(row,id)

	self._index_document(k,i)

    def _reindex(self,start=0):
	"""Recompute index data for data with ids >= start."""
	for i in self._data.keys(start): self.index_item(i)

    def _index_document(self, document_text, id):
        src = WordSequence(document_text, self._syn)  

        d = {}
        i = -1
	__traceback_info__= document_text, id
	try:
	    for s in src:
		i = i + 1
		
		if s[0] == '\"': self.subindex(s[1:-1],d,i)
		else:
		    try: d[s].append(i)
		    except KeyError: d[s] = [ i ]
	except: pass

        if (i < 1): return

	self._id2info[id]=i,d

	w2ids=self._w2ids
        for word in d.keys():
	    try: r=w2ids[word]
	    except KeyError:
		r=w2ids[word]=intSet()
	    r.insert(id)

    def unindex_item(self, id):
	del self._id2info[id]

    def _subindex(self, isrc, d, pos):

        src = WordSequence(isrc, self._syn)  

        for s in src:
	    if s[0] == '\"':
		self.subindex(s[1:-1],d,pos)
	    else:
		try:
		    d[s].append(pos)
		except KeyError:
		    d[s] = [ pos ]
  

    def __getitem__(self, word):
	"""Return an InvertedIndex-style result "list"
	"""
	r=ResultList()
	try: set=self._w2ids[word]
	except: return r

	info=self._id2info
	for id in set:
	    try:
		v=info[id]
		r[id]=v[0],v[1][word]
	    except: pass

	return r

    def _apply_index(self, request,ListType=[]):
	"""Apply the index to query parameters given in the argument, request

	The argument should be a mapping object.

	If the request does not contain the needed parameters, then None is
	returned.

	Otherwise two objects are returned.  The first object is a
	ResultSet containing the record numbers of the matching
	records.  The second object is a tuple containing the names of
	all data fields used.

	"""
	id=self.id
	try: keys=request[id]
	except: return None

	if type(keys) is not ListType: keys=[keys]
	r=None
	for key in keys:
	    key=strip(key)
	    if not key: continue
	    rr=intSet()
	    try:
		for i in query(key,self).keys():
		    rr.insert(i)
	    except KeyError: pass
	    if r is None: r=rr
	    else:
		# Note that we *and*/*narrow* multiple search terms.
		r=r.intersection(rr) 

	if r is not None: return r, (id,)
	
    


############################################################################## 
#
# $Log: TextIndex.py,v $
# Revision 1.3  1997/09/17 17:53:32  jim
# Added unindex_item.
# This thing needs an overhaul; already. :-(
#
# Revision 1.2  1997/09/12 14:25:40  jim
# Added logic to allow "blank" inputs.
#
# Revision 1.1  1997/09/11 22:19:09  jim
# *** empty log message ***
#
#
