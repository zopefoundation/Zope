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



$Id: TextIndex.py,v 1.9 1998/02/05 15:24:22 jim Exp $'''
__version__='$Revision: 1.9 $'[11:-2]

from Globals import Persistent
import BTree, IIBTree
BTree=BTree.BTree
IIBTree=IIBTree.Bucket
from intSet import intSet
import operator
getitem=operator.__getitem__
from Splitter import Splitter
from string import strip
import string, regex, regsub

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
	self._index=BTree()
	self._syn=stop_word_dict
	self._reindex()

    def clear(self):
	self._index=BTree()

    def positions(self, docid, words):
	"""Return the positions in the document for the given document
	id of the word, word."""
	id=self.id
	if self._schema is None:
	    f=getattr
	else:
	    f=getitem
	    id=self._schema[id]

	row=self._data[docid]
	doc=str(f(row,id))
	r=[]
	for word in words:
	    r=r+Splitter(doc, self._syn).indexes(word)
	return r

    def index_item(self,i,un=0):
	"""Recompute index data for data with ids >= start."""

	id=self.id
	if self._schema is None:
	    f=getattr
	else:
	    f=getitem
	    id=self._schema[id]

	row=self._data[i]
	k=str(f(row,id))

	self._index_document(k,i,un)

    def unindex_item(self, i): return self.index_item(i,1)

    def _reindex(self,start=0):
	"""Recompute index data for data with ids >= start."""
	for i in self._data.keys(start): self.index_item(i)

    def _index_document(self, document_text, id, un=0,
			tupleType=type(()),
			dictType=type({}),
			):
        src = Splitter(document_text, self._syn)  

        d = {}
	old=d.has_key
	last=None
	
	for s in src:
	    if s[0] == '\"': last=self.subindex(s[1:-1],d,old,last)
	    else:
		if old(s):
		    if s != last: d[s]=d[s]+1
		else: d[s]=1

	index=self._index
	indexed=index.has_key
	if un:
	    for word,score in d.items():
		if indexed(word):
		    r=index[word]
		    if type(r) is tupleType: del index[word]
		    else:
			if r.has_key(id): del r[id]
			if type(r) is dictType:
			    if len(r) < 2:
				if r:
				    for k, v in r.items(): index[word]=k,v
				else: del index[word]
			    else: index[word]=r
	else:
	    for word,score in d.items():
		if indexed(word):
		    r=index[word]
		    if type(r) is tupleType:
			r={r[0]:r[1]}
			r[id]=score
			index[word]=r
		    elif type(r) is dictType:
			if len(r) > 4:
			    b=IIBTree()
			    for k, v in r.items(): b[k]=v
			    r=b
			r[id]=score
			index[word]=r
		    else: r[id]=score
		else: index[word]=id,score

    def _subindex(self, isrc, d, old, last):

        src = Splitter(isrc, self._syn)  

	for s in src:
	    if s[0] == '\"': last=self.subindex(s[1:-1],d,old,last)
	    else:
		if old(s):
		    if s != last: d[s]=d[s]+1
		else: d[s]=1

	return last

    def __getitem__(self, word):
	"""Return an InvertedIndex-style result "list"
	"""
        src = tuple(Splitter(word, self._syn))
	if len(src) == 1:
	    src=src[0]
	    if src[:1]=='"' and src[-1:]=='"': return self[src]
	    index=self._index
	    if index.has_key(word): r=self._index[word]
	    else: r={}
	    return ResultList(r,(word,),self)
	    
	r=None
	for word in src:
	    rr=self[word]
	    if r is None: r=rr
	    else: r=r.near(rr)

	return r

    def _apply_index(self, request, cid='', ListType=[]):
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

	cidid="%s/%s" % (cid,id)
	has_key=request.has_key
	if has_key(cidid): keys=request[cidid]
	elif has_key(id): keys=request[id]
	else: return None

	if type(keys) is not ListType: keys=[keys]
	r=None
	for key in keys:
	    key=strip(key)
	    if not key: continue
	    rr=intSet()
	    try:
		for i,score in query(key,self).items():
		    if score: rr.insert(i)
	    except KeyError: pass
	    if r is None: r=rr
	    else:
		# Note that we *and*/*narrow* multiple search terms.
		r=r.intersection(rr) 

	if r is not None: return r, (id,)
	

class ResultList:
  
    def __init__(self, d, words, index, TupleType=type(())):
	self._index=index
	self._words=words
        if (type(d) is TupleType): self._dict = { d[0] : d[1] }
        else: self._dict = d
    
    def __len__(self): return len(self._dict)
    def __getitem__(self, key): return self._dict[key]
    def keys(self): return self._dict.keys()
    def has_key(self, key): return self._dict.has_key(key)
    def items(self): return self._dict.items()  

    def __and__(self, x):
        result = {}
	dict=self._dict
	xdict=x._dict
	xhas=xdict.has_key
        for id, score in dict.items():
	    if xhas(id): result[id]=xdict[id]+score
    
        return self.__class__(result, self._words+x._words, self._index)

    def and_not(self, x):
        result = {}
	dict=self._dict
	xdict=x._dict
	xhas=xdict.has_key
        for id, score in dict.items():
	    if not xhas(id): result[id]=xdict[id]+score
    
        return self.__class__(result, self._words, self._index)
  
    def __or__(self, x):
        result = {}
	dict=self._dict
	has=dict.has_key
	xdict=x._dict
	xhas=xdict.has_key
        for id, score in dict.items():
	    if xhas(id): result[id]=xdict[id]+score
	    else: result[id]=score

	for id, score in xdict.items():
	    if not has(id): result[id]=score
    
        return self.__class__(result, self._words+x._words, self._index)

    def near(self, x):
        result = {}
	dict=self._dict
	xdict=x._dict
	xhas=xdict.has_key
	positions=self._index.positions
        for id, score in dict.items():
	    if not xhas(id): continue
	    p=(map(lambda i: (i,0), positions(id,self._words))+
	       map(lambda i: (i,1), positions(id,x._words)))
	    p.sort()
	    d=lp=9999
	    li=None
	    lsrc=None
	    for i,src in p:
		if i is not li and src is not lsrc and li is not None:
		    d=min(d,i-li)
		li=i
		lsrc=src
	    if d==lp: score=min(score,xdict[id]) # synonyms
	    else: score=(score+xdict[id])/d
	    result[id]=score
    
        return self.__class__(result, self._words+x._words, self._index)



AndNot    = 'andnot'
And       = 'and'
Or        = 'or'
Near = '...'
QueryError='TextIndex.QueryError'

def query(s, index, default_operator = Or,
	  ws = (string.whitespace,)):
    # First replace any occurences of " and not " with " andnot "
    s = regsub.gsub('[%s]+and[%s]*not[%s]+' % (ws * 3), ' andnot ', s)
    q = parse(s)
    q = parse2(q, default_operator)
    return evaluate(q, index)

def parse(s):
    '''Parse parentheses and quotes'''
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
	   operator_dict = {AndNot: AndNot, And: And, Or: Or, Near: Near},
	   ListType=type([]),
	   ):
    '''Find operators and operands'''
    i = 0
    isop=operator_dict.has_key
    while (i < len(q)):
        if (type(q[i]) is ListType): q[i] = parse2(q[i], default_operator)

        # every other item, starting with the first, should be an operand
        if ((i % 2) != 0):
            # This word should be an operator; if it is not, splice in
            # the default operator.
	    
	    if isop(q[i]): q[i] = operator_dict[q[i]]
            else: q[i : i] = [ default_operator ]

        i = i + 1

    return q

def parens(s, parens_regex = regex.compile("(\|)")):
    '''Find the beginning and end of the first set of parentheses'''

    if (parens_regex.search(s) < 0): return None

    if (parens_regex.group(0) == ")"):
	raise QueryError, "Mismatched parentheses"

    open = parens_regex.regs[0][0] + 1
    start = parens_regex.regs[0][1]
    p = 1

    while (parens_regex.search(s, start) >= 0):
	if (parens_regex.group(0) == ")"): p = p - 1
        else: p = p + 1

	start = parens_regex.regs[0][1]
  
        if (p == 0): return (open, parens_regex.regs[0][0])

    raise QueryError, "Mismatched parentheses"    

def quotes(s, ws = (string.whitespace,)):
     # split up quoted regions
     splitted = regsub.split(s, '[%s]*\"[%s]*' % (ws * 2))
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

def get_operands(q, i, index, ListType=type([]), StringType=type('')):
    '''Evaluate and return the left and right operands for an operator'''
    try:
        left  = q[i - 1]
        right = q[i + 1]
    except IndexError: raise QueryError, "Malformed query"

    t=type(left)
    if t is ListType: left = evaluate(left, index)
    elif t is StringType: left=index[left]

    t=type(right)
    if t is ListType: right = evaluate(right, index)
    elif t is StringType: right=index[right]

    return (left, right)

def evaluate(q, index,ListType=type([])):
    '''Evaluate a parsed query'''

    if (len(q) == 1):
	if (type(q[0]) is ListType):
	    return evaluate(q[0], index)

        return index[q[0]]
      
    i = 0
    while (i < len(q)):
        if q[i] is AndNot:
            left, right = get_operands(q, i, index)
            val = left.and_not(right)
            q[(i - 1) : (i + 2)] = [ val ]
        else: i = i + 1

    i = 0
    while (i < len(q)):
        if q[i] is And:
	    left, right = get_operands(q, i, index)
	    val = left & right
	    q[(i - 1) : (i + 2)] = [ val ]
        else: i = i + 1

    i = 0
    while (i < len(q)):
        if q[i] is Or:
	    left, right = get_operands(q, i, index)
	    val = left | right
	    q[(i - 1) : (i + 2)] = [ val ]
	else: i = i + 1

    i = 0
    while (i < len(q)):
        if q[i] is Near:
	    left, right = get_operands(q, i, index)
	    val = left.near(right)
	    q[(i - 1) : (i + 2)] = [ val ]
        else: i = i + 1

    if (len(q) != 1): raise QueryError, "Malformed query"

    return q[0]


stop_words=(
    'am', 'ii', 'iii', 'per', 'po', 're', 'a', 'about', 'above', 'across',
    'after', 'afterwards', 'again', 'against', 'all', 'almost', 'alone',
    'along', 'already', 'also', 'although', 'always', 'am', 'among',
    'amongst', 'amoungst', 'amount', 'an', 'and', 'another', 'any',
    'anyhow', 'anyone', 'anything', 'anyway', 'anywhere', 'are', 'around',
    'as', 'at', 'back', 'be', 'became', 'because', 'become', 'becomes',
    'becoming', 'been', 'before', 'beforehand', 'behind', 'being',
    'below', 'beside', 'besides', 'between', 'beyond', 'bill', 'both',
    'bottom', 'but', 'by', 'can', 'cannot', 'cant', 'con', 'could',
    'couldnt', 'cry', 'describe', 'detail', 'do', 'done', 'down', 'due',
    'during', 'each', 'eg', 'eight', 'either', 'eleven', 'else',
    'elsewhere', 'empty', 'enough', 'even', 'ever', 'every', 'everyone',
    'everything', 'everywhere', 'except', 'few', 'fifteen', 'fify',
    'fill', 'find', 'fire', 'first', 'five', 'for', 'former', 'formerly',
    'forty', 'found', 'four', 'from', 'front', 'full', 'further', 'get',
    'give', 'go', 'had', 'has', 'hasnt', 'have', 'he', 'hence', 'her',
    'here', 'hereafter', 'hereby', 'herein', 'hereupon', 'hers',
    'herself', 'him', 'himself', 'his', 'how', 'however', 'hundred', 'i',
    'ie', 'if', 'in', 'inc', 'indeed', 'interest', 'into', 'is', 'it',
    'its', 'itself', 'keep', 'last', 'latter', 'latterly', 'least',
    'less', 'made', 'many', 'may', 'me', 'meanwhile', 'might', 'mill',
    'mine', 'more', 'moreover', 'most', 'mostly', 'move', 'much', 'must',
    'my', 'myself', 'name', 'namely', 'neither', 'never', 'nevertheless',
    'next', 'nine', 'no', 'nobody', 'none', 'noone', 'nor', 'not',
    'nothing', 'now', 'nowhere', 'of', 'off', 'often', 'on', 'once',
    'one', 'only', 'onto', 'or', 'other', 'others', 'otherwise', 'our',
    'ours', 'ourselves', 'out', 'over', 'own', 'per', 'perhaps',
    'please', 'pre', 'put', 'rather', 're', 'same', 'see', 'seem',
    'seemed', 'seeming', 'seems', 'serious', 'several', 'she', 'should',
    'show', 'side', 'since', 'sincere', 'six', 'sixty', 'so', 'some',
    'somehow', 'someone', 'something', 'sometime', 'sometimes',
    'somewhere', 'still', 'such', 'take', 'ten', 'than', 'that', 'the',
    'their', 'them', 'themselves', 'then', 'thence', 'there',
    'thereafter', 'thereby', 'therefore', 'therein', 'thereupon', 'these',
    'they', 'thick', 'thin', 'third', 'this', 'those', 'though', 'three',
    'through', 'throughout', 'thru', 'thus', 'to', 'together', 'too',
    'toward', 'towards', 'twelve', 'twenty', 'two', 'un', 'under',
    'until', 'up', 'upon', 'us', 'very', 'via', 'was', 'we', 'well',
    'were', 'what', 'whatever', 'when', 'whence', 'whenever', 'where',
    'whereafter', 'whereas', 'whereby', 'wherein', 'whereupon',
    'wherever', 'whether', 'which', 'while', 'whither', 'who', 'whoever',
    'whole', 'whom', 'whose', 'why', 'will', 'with', 'within', 'without',
    'would', 'yet', 'you', 'your', 'yours', 'yourself', 'yourselves',
    )
stop_word_dict={}
for word in stop_words: stop_word_dict[word]=None


############################################################################## 
#
# $Log: TextIndex.py,v $
# Revision 1.9  1998/02/05 15:24:22  jim
# Got rid of most try/excepts.
#
# Revision 1.8  1997/12/02 19:36:19  jeffrey
# fixed bug in .clear() method
#
# Revision 1.7  1997/12/01 22:58:48  jeffrey
# Allow indexing of non-text fields
#
# Revision 1.6  1997/11/03 18:59:59  jim
# Fixed several bugs in handling query parsing and proximity search.
#
# Revision 1.5  1997/11/03 15:17:12  jim
# Updated to use new indexing strategy.  Now, no longer store positions
# in index, but get them on demand from doc.
#
# Removed vestiges of InvertedIndex.
#
# Revision 1.4  1997/09/26 22:21:44  jim
# added protocol needed by searchable objects
#
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
