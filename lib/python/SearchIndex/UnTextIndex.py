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
__version__='$Revision: 1.27 $'[11:-2]

from Globals import Persistent
import BTree, IIBTree, IOBTree, OIBTree
from Acquisition import Implicit
BTree=BTree.BTree
IOBTree=IOBTree.BTree
IIBucket=IIBTree.Bucket
OIBTree=OIBTree.BTree
from intSet import intSet
import operator
from Splitter import Splitter
from string import strip
import string, regex, regsub, ts_regex
from zLOG import LOG, ERROR


from Lexicon import Lexicon, stop_word_dict
from ResultList import ResultList


AndNot    = 'andnot'
And       = 'and'
Or        = 'or'
Near = '...'
QueryError='TextIndex.QueryError'

            

class UnTextIndex(Persistent, Implicit):

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
          index will use a private lexicon.

        There is a ZCatalog UML model that sheds some light on what is
        going on here.  '_index' is a BTree which maps word ids to
        mapping from document id to score.  Something like:

          {'bob' : {1 : 5, 2 : 3, 42 : 9}}
          {'uncle' : {1 : 1}}


        The '_unindex' attribute is a mapping from document id to word 
        ids.  This mapping allows the catalog to unindex an object:

          {42 : ('bob', 'is', 'your', 'uncle')

        This isn't exactly how things are represented in memory, many
        optimizations happen along the way.

        """
        if not id==ignore_ex==call_methods==None:
            self.id=id
            self.ignore_ex=ignore_ex
            self.call_methods=call_methods
            self._index=IOBTree()
            self._unindex=IOBTree()

        else:
            pass

        if lexicon is None:

            ## if no lexicon is provided, create a dumb one
            self._lexicon=Lexicon()
        else:
            self._lexicon = lexicon


    def __setstate(self, state):
        Persistent.__setstate__(self, state)
        if hasattr(self, '_syn'):
            del self._syn

    def getLexicon(self, vocab_id):
        
        """ bit of a hack, indexes have been made acquirers so that
        they can acquire a vocabulary object from the object system in 
        Zope.  I don't think indexes were ever intended to participate 
        in this way, but I don't see too much of a problem with it.
        """
        if type(vocab_id) is not type(""):
            vocab = vocab_id
        else:
            vocab = getattr(self, vocab_id)
        return vocab.lexicon
        

    def __len__(self):
        return len(self._unindex)

##    def __setstate__(self, state):
##        Persistent.__setstate__(self, state)
##        if not hasattr(self, '_lexicon'):
##            self._lexicon = Lexicon()
        

    def clear(self):
        self._index = IOBTree()
        self._unindex = IOBTree()


    def index_object(self, i, obj, threshold=None, tupleType=type(()),
                     dictType=type({}), strType=type(""), callable=callable):
        
        """ Index an object:

          'i' is the integer id of the document

          'obj' is the objects to be indexed

          'threshold' is the number of words to process between
          commiting subtransactions.  If 'None' subtransactions are
          not used.

          the next four arguments are default optimizations.
          """

        id = self.id
        try:
            ## sniff the object for our 'id', the 'document source' of 
            ## the index is this attribute.  If it smells callable,
            ## call it.
            k = getattr(obj, id)
            if callable(k):
                k = str(k())
            else:
                k = str(k)
        except:
            return 0
        
        d = OIBTree()
        old = d.has_key
        last = None

        ## The Splitter should now be european compliant at least.
        ## Someone should test this.

##        import pdb
##        pdb.set_trace()
        
        src = self.getLexicon(self._lexicon).Splitter(k)
        ## This returns a tuple of stemmed words.  Stopwords have been 
        ## stripped.
        
        for s in src:
            if s[0] == '\"': last=self.subindex(s[1:-1], d, old, last)
            else:
                if old(s):
                    if s != last: d[s] = d[s]+1
                else: d[s] = 1

        index = self._index
        unindex = self._unindex
        lexicon = self.getLexicon(self._lexicon)
        get = index.get
        unindex[i] = []
        times = 0

        for word, score in d.items():
            if threshold is not None:
                if times > threshold:
                    # commit a subtransaction hack
                    get_transaction().commit(1)
                    # kick the cache
                    self._p_jar.cacheFullSweep(1)
                    times = 0
                    
            word_id = lexicon.set(word)
            
            r = get(word_id)
            if r is not None:
                r = index[word_id]
                if type(r) is tupleType:
                    r = {r[0]:r[1]}
                    r[i] = score

                    index[word_id] = r
                    unindex[i].append(word_id)
                    
                elif type(r) is dictType:
                    if len(r) > 4:
                        b = IIBucket()
                        for k, v in r.items(): b[k] = v
                        r = b
                    r[i] = score

                    index[word_id] = r
                    unindex[i].append(word_id)
                    
                else:
                    r[i] = score
                    unindex[i].append(word_id)
            else:
                index[word_id] = i, score
                unindex[i].append(word_id)
            times = times + 1

        unindex[i] = tuple(unindex[i])
        l = len(unindex[i])
        
        self._index = index
        self._unindex = unindex

        ## return the number of words you indexed
        return times

    def unindex_object(self, i, tt=type(()) ): 
        """ carefully unindex document with integer id 'i' from the text
        index and do not fail if it does not exist """
        index = self._index
        unindex = self._unindex
        val = unindex.get(i, None)
        if val is not None:
            for n in val:
                v = index.get(n, None)
                if type(v) is tt:
                    del index[n]
                elif v is not None:
                    try:
                        del index[n][i]
                    except (KeyError, IndexError, TypeError):
                        LOG('UnTextIndex', PROBLEM,
                            'unindex_object tried to unindex nonexistent'
                            ' document %s' % str(i))
            del unindex[i]
            self._index = index
            self._unindex = unindex

    def __getitem__(self, word):
        """Return an InvertedIndex-style result "list"
        """
        src = tuple(self.getLexicon(self._lexicon).Splitter(word))
        if not src: return ResultList({}, (word,), self)
        if len(src) == 1:
            src=src[0]
            if src[:1]=='"' and src[-1:]=='"': return self[src]
            r = self._index.get(self.getLexicon(self._lexicon).get(src)[0],
                                None)
            if r is None: r = {}
            return ResultList(r, (src,), self)
            
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

        if request.has_key(id):
            keys = request[id]
        else:
            return None

        if type(keys) is type(''):
            if not keys or not strip(keys):
                return None
            keys = [keys]
        r = None
        
        for key in keys:
            key = strip(key)
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
            return r, (id,)
        return IIBucket(), (id,)


    def positions(self, docid, words, obj):
        """Return the positions in the document for the given document
        id of the word, word."""
        id = self.id

        if self._schema is None:
            f = getattr
        else:
            f = operator.__getitem__
            id = self._schema[id]


        if self.call_methods:
            doc = str(f(obj, id)())
        else:
            doc = str(f(obj, id))

        r = []
        for word in words:
            r = r+self.getLexicon(self._lexicon).Splitter(doc).indexes(word)
        return r


    def _subindex(self, isrc, d, old, last):

        src = self.getLexicon(self._lexicon).Splitter(isrc)  

        for s in src:
            if s[0] == '\"': last=self.subindex(s[1:-1],d,old,last)
            else:
                if old(s):
                    if s != last: d[s] = d[s]+1
                else: d[s] = 1

        return last


    def query(self, s, default_operator = Or, ws = (string.whitespace,)):
        """

        This is called by TextIndexes.  A 'query term' which is a string
        's' is passed in, along with an index object.  s is parsed, then
        the wildcards are parsed, then something is parsed again, then the 
        whole thing is 'evaluated'

        """

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


    def get_operands(self, q, i, ListType=type([]), StringType=type('')):
        '''Evaluate and return the left and right operands for an operator'''
        try:
            left  = q[i - 1]
            right = q[i + 1]
        except IndexError: raise QueryError, "Malformed query"

        t=type(left)
        if t is ListType: left = evaluate(left, self)
        elif t is StringType: left=self[left]

        t=type(right)
        if t is ListType: right = evaluate(right, self)
        elif t is StringType: right=self[right]

        return (left, right)


    def evaluate(self, q, ListType=type([])):
        '''Evaluate a parsed query'''
    ##    import pdb
    ##    pdb.set_trace()

        if (len(q) == 1):
            if (type(q[0]) is ListType):
                return evaluate(q[0], self)

            return self[q[0]]

        i = 0
        while (i < len(q)):
            if q[i] is AndNot:
                left, right = self.get_operands(q, i)
                val = left.and_not(right)
                q[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        i = 0
        while (i < len(q)):
            if q[i] is And:
                left, right = self.get_operands(q, i)
                val = left & right
                q[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        i = 0
        while (i < len(q)):
            if q[i] is Or:
                left, right = self.get_operands(q, i)
                val = left | right
                q[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        i = 0
        while (i < len(q)):
            if q[i] is Near:
                left, right = self.get_operands(q, i)
                val = left.near(right)
                q[(i - 1) : (i + 2)] = [ val ]
            else: i = i + 1

        if (len(q) != 1): raise QueryError, "Malformed query"

        return q[0]


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
            
            if type(q[i]) is not ListType and isop(q[i]):
                q[i] = operator_dict[q[i]]
            else: q[i : i] = [ default_operator ]

        i = i + 1

    return q


def parens(s, parens_re = regex.compile('(\|)').search):

    index=open_index=paren_count = 0

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



def quotes(s, ws = (string.whitespace,)):
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
