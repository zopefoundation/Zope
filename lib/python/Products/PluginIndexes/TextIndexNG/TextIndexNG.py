##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

"""
Text Index
"""

__version__ = '$Revision: 1.1 $'[11:-2]

import  re
import warnings
from Globals import Persistent,DTMLFile
from zLOG import LOG, ERROR
from OFS.SimpleItem import SimpleItem
from Acquisition import Implicit
from Products.PluginIndexes.TextIndexNG.ResultListNG import ResultListNG
from Products.PluginIndexes import PluggableIndex       
from Products.PluginIndexes.common.util import parseIndexRequest

from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.OOBTree import OOBTree
from BTrees.IIBTree import IIBTree, IIBucket, IISet, IITreeSet
from BTrees.IIBTree import difference, weightedIntersection

from Products.PluginIndexes.TextIndex.Lexicon import Lexicon
from Products.PluginIndexes.TextIndex.GlobbingLexicon import GlobbingLexicon

from Products.PluginIndexes.TextIndex import Splitter

import Stemmer

from types import IntType, StringType, UnicodeType
from TextOperators import *
from TextIndexCommon import *


class TextIndexNG(PluggableIndex.PluggableIndex, Persistent,
     Implicit, SimpleItem):

    __implements__ = (PluggableIndex.PluggableIndexInterface,)

    meta_type='TextIndexNG'

    manage_options= (
        {'label': 'Settings',     
         'action': 'manage_main',
         'help': ('TextIndex','TextIndex_Settings.stx')},
    )

    query_options = ["query","operator"]
 
    def __init__(self 
                 , id 
                 , extra= None
                 , caller = None
                ):

        self.id            = id

        self.useSplitter   = getattr(extra,'useSplitter',   'ZopeSplitter')
        self.useStemmer    = getattr(extra,'useStemmer',    None)
        self.useOperator   = getattr(extra,'useOperator',   'and')
        self.useGlobbing   = getattr(extra,'useGlobbing',   1)
        self.lexicon       = getattr(extra,'lexicon',       None)
        self.useNearSearch = getattr(extra,'useNearSearch', 1)
        self.nearDistance  = getattr(extra,'nearDistance',  5)

        if self.lexicon== 'None':     self.lexicon    = None
        if self.useStemmer == 'None': self.useStemmer = None

        self.clear()
                        

    def clear(self):

        self._IDX     = IOBTree()

        # get splitter function
        self._splitterfunc = self._stemmerfunc = None

        if self.useSplitter:
            self._splitterfunc = Splitter.getSplitter(self.useSplitter)

        # stemmer function
        if self.useStemmer:
            self._stemmerfunc = Stemmer.Stemmer(self.useStemmer).stem

        if self.lexicon:
            self._LEXICON = self.lexicon
        else:
            if self.useGlobbing:
                self._LEXICON = GlobbingLexicon()
                debug('created new globbing lexicon')
                if self._stemmerfunc:
                    debug('stemming disabled because globbing enabled')
                    self._stemmerfunc = None

            else:
                self._LEXICON = Lexicon()
                debug('created new lexicon')


        self._v_getWordId      = self._LEXICON.getWordId
        self._v_getWordById    = self._LEXICON.getWord
        self._v_getIdByWord    = self._LEXICON.get

    def __nonzero__(self):
        return not not self._unindex
    

    def insertForwardEntry(self,wordId,pos,documentId):

        # self._IDX is a mapping:
        # wordId -> documentId -> [positions]
        
        idx = self._IDX

        if idx.has_key(wordId) == 0:
            idx[wordId] = IOBTree()

        tree = idx[wordId] 
        if tree.has_key(documentId) == 0:
            tree[documentId] = IISet() 

        tree[documentId].insert(pos)



    def _printIndex(self):

        for wordId in self._IDX.keys():
            print '-'*78
            print wordId,self._v_getWordById(wordId),
            print 
            for k,v in self._IDX[wordId].items():
                print k,v

    def index_object(self, documentId, obj, threshold=None):

        try:
            source = getattr(obj, self.id)
            if callable(source): source = str(source())
            else:                source = str(source)
        except (AttributeError, TypeError):
            return 0

        # sniff the object for 'id'+'_encoding'
        
        try:
            encoding = getattr(obj, self.id+'_encoding')
            if callable(encoding ):
                encoding = str(encoding())
            else:
                encoding = str(encoding)
        except (AttributeError, TypeError):
            encoding = 'latin1'


        # Split the text into a list of words
        words = self._splitterfunc(source,encoding=encoding)
    
        for i in range(len(words)):
            word = words[i]

            # stem the single word        
            if self._stemmerfunc:
                word = self._stemmerfunc(word)

            # get (new) wordId for word
            wid = self._v_getWordId(word)

            # and insert the wordId, its position and the documentId 
            # in the index
            self.insertForwardEntry(wid,i,documentId)


    def __getitem__(self, word):
        """Return an InvertedIndex-style result "list"

        Note that this differentiates between being passed an Integer
        and a String.  Strings are looked up in the lexicon, whereas
        Integers are assumed to be resolved word ids. """

        if isinstance(word, IntType):

            # We have a word ID

            r = {}

            res = self._IDX.get(word, None)

            for docId in  res.keys():
                r[docId] = self._IDX[word][docId]

            return ResultListNG(r , (word,), self)

        else:

            # We need to stem

            if self._stemmerfunc:
                word = self._stemmerfunc(word)

            wids = self._v_getIdByWord(word)

            if wids:
                r = {}

                res  = self._IDX.get(wids[0], None)
                for docId in  res.keys():
                    r[docId] = self._IDX[wids[0]][docId]

            else:
                r={}

            return ResultListNG(r, (word,), self)


    def getLexicon(self):
        return self._LEXICON


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

        record = parseIndexRequest(request,self.id,self.query_options)
        if record.keys==None: return None

        # Changed for 2.4
        # We use the default operator that can me managed via the ZMI

        qop = record.get('operator', self.useOperator)
        query_operator = operator_dict.get(qop)

        if query_operator is None:
            raise exceptions.RuntimeError, ("Invalid operator '%s' "
                                            "for a TextIndex" % qop)
        r = None

        for key in record.keys:
            key = key.strip()
            if not key:
                continue

            b = self.query(key, query_operator)
            w, r = weightedIntersection(r, b)

        if r is not None:
            return r, (self.id,)
        
        return (IIBucket(), (self.id,))


    def positions(self,docId, words):
        """ search all positions for a list of words for
            a given document given by its documentId.
            positions() returns a mapping word to
            list of positions of the word inside the document.
        """
      
        debug('searching positions docid: %s, words: %s' % (docId,words))

        res = OOBTree()

        for w in words:

            if isinstance(w,IntType):
                wid = w
                word = self._v_getWordById(w) 
            else:
                wid = self._v_getIdByWord(w)[0]
                word = w

            if self._IDX[wid].has_key(docId):
                res[w] = self._IDX[wid][docId]


        for k,v in res.items():
            debug(k,v)

        return res


    def query(self, s, default_operator=Or):
        """ Evaluate a query string.
        
        Convert the query string into a data structure of nested lists
        and strings, based on the grouping of whitespace-separated
        strings by parentheses and quotes.  The 'Near' operator is
        inserted between the strings of a quoted group.

        The Lexicon is given the opportunity to transform the
        data structure.  Stemming, wildcards, and translation are
        possible Lexicon services.

        Finally, the query list is normalized so that it and every
        sub-list consist of non-operator strings or lists separated
        by operators. This list is evaluated.
        """

        # First replace any occurences of " and not " with " andnot "
        s = re.sub('(?i)\s+and\s*not\s+', ' andnot ', s)

        # Parse parentheses and quotes
        q = parse(s)

        # Allow the Lexicon to process the query
        q = self.getLexicon().query_hook(q)

        # Insert the default operator between any two search terms not
        # already joined by an operator.
        q = parse2(q, default_operator)
        debug('before eval',q)

        # evalute the final 'expression'
        return self.evaluate(q)


    def get_operands(self, q, i):

        """Evaluate and return the left and right operands for an operator"""

        try:
            left  = q[i - 1]
            right = q[i + 1]
        except IndexError:
            raise QueryError, "Malformed query"

        if isinstance(left, IntType):
            left = self[left]
        elif isinstance(left, StringType) or isinstance(left,UnicodeType):
            left = self[left]        
        elif isinstance(left, ListType):
            left = self.evaluate(left)

        if isinstance(right, IntType):
            right = self[right]
        elif isinstance(right, StringType) or isinstance(right,UnicodeType):
            right = self[right]       
        elif isinstance(right, ListType):
            right = self.evaluate(right)

        return (left, right)



    def evaluate(self, query):
        """Evaluate a parsed query"""

        # Strip off meaningless layers
        while isinstance(query, ListType) and len(query) == 1:
            query = query[0]

        # If it's not a list, assume a string or number
        if not isinstance(query, ListType):
            return self[query]

        # Now we need to loop through the query and reduce
        # operators.  They are currently evaluated in the following
        # order: AndNot -> And -> Or -> Near
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

        if (len(query) != 1):
            raise QueryError, "Malformed query"

        return query[0]


    def numObjects(self):
        """ return number of index objects """
        return len(self._IDX)


    def manage_setPreferences(self,extra,
                               REQUEST=None,RESPONSE=None,URL2=None):
        """ preferences of TextIndex """

        pass

        if RESPONSE:
            RESPONSE.redirect(URL2 + '/manage_main?manage_tabs_message=Preferences%20saved')


    manage_workspace  = DTMLFile("dtml/manageTextIndexNG",globals())


manage_addTextIndexNGForm = DTMLFile('dtml/addTextIndexNG', globals())

def manage_addTextIndexNG(self, id, extra, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a new TextIndexNG """
    return self.manage_addIndex(id, 'TextIndexNG', extra, REQUEST, RESPONSE, URL3)

