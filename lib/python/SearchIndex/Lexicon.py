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

import string, regex, ts_regex
import regsub



__doc__=""" Module breaks out Zope specific methods and behavior.  In
addition, provides the Lexicon class which defines a word to integer
mapping.

"""

from Splitter import Splitter
from Persistence import Persistent
from Acquisition import Implicit
import OIBTree, BTree
OIBTree=OIBTree.BTree
OOBTree=BTree.BTree
import re


class Lexicon(Persistent, Implicit):
    """ maps words to word ids and then some

    The Lexicon object is an attempt to abstract voacbularies out of
    Text indexes.  This abstraction is not totally cooked yet, this
    module still includes the parser for the 'Text Index Query
    Language' and a few other hacks.

    """

    def __init__(self):
        self._lexicon = OIBTree()

    def set(self, word):
        """ return the word id of 'word' """

        if self._lexicon.has_key(word):
            return self._lexicon[word]

        else:
            self._lexicon[intern(word)] = self.counter
            self.counter = self.counter + 1
            return self.counter

    def get(self, key):
        """  """
        return self._lexicon[key]

    def __len__(self):
        return len(self._lexicon)

    def Splitter(self, astring, words):
        """ wrap the splitter """
        return Splitter(astring, words)

    def grep(self, query):
        """
        regular expression search through the lexicon
        he he.

        Do not use unless you know what your doing!!!
        """
        expr = re.compile(query)
        hits = []
        for x in self._lexicon.keys():
            if expr.search(x):
                hits.append(x)
        return hits







AndNot    = 'andnot'
And       = 'and'
Or        = 'or'
Near = '...'
QueryError='TextIndex.QueryError'

def query(s, index, default_operator = Or,
          ws = (string.whitespace,)):
    # First replace any occurences of " and not " with " andnot "
    s = ts_regex.gsub('[%s]+and[%s]*not[%s]+' % (ws * 3), ' andnot ', s)
    q = parse(s)
    q = parse_wc(q, index)
    q = parse2(q, default_operator)
    return evaluate(q, index)

def parse_wc(q, index):
    '''expand wildcards'''
    lex = index.getLexicon(index._lexicon)
    words = []
    for w in q:
        if ( (lex.multi_wc in w) or
            (lex.single_wc in w) ):
            wids = lex.query(w)
            for wid in wids:
                if words:
                    words.append(Or)
                words.append(lex._inverseLex[wid])
        else:
            words.append(w)

    return words
            
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

def evaluate(q, index, ListType=type([])):
    '''Evaluate a parsed query'''
##    import pdb
##    pdb.set_trace()

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
    'everything', 'everywhere', 'except', 'few', 'fifteen', 'fifty',
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




