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


    def __init__(self, stop_syn=None):
        self._lexicon = OIBTree()
        self.counter = 0
        if stop_syn is None:
            self.stop_syn = {}
        else:
            self.stop_syn = {}

                
    def set_stop_syn(selfb, stop_syn):
        """ pass in a mapping of stopwords and synonyms.  Format is:

        {'word' : [syn1, syn2, ..., synx]}

        Vocabularies do not necesarily need to implement this if their
        splitters do not support stemming or stoping.

        """
        self.stop_syn = stop_syn
        

    def set(self, word):
        """ return the word id of 'word' """

        if self._lexicon.has_key(word):
            return self._lexicon[word]

        else:
            if not hasattr(self, 'counter'):
                self.counter = 0
            self._lexicon[intern(word)] = self.counter
            self.counter = self.counter + 1
            return self.counter - 1 

    def get(self, key):
        """  """
        return [self._lexicon[key]]

    def __getitem__(self, key):
        return self.get(key)

    def __len__(self):
        return len(self._lexicon)

    def Splitter(self, astring, words=None):
        """ wrap the splitter """

        if words is None:
            word = self.stop_syn
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

    def query_hook(self, q):
        """ we don't want to modify the query cuz we're dumb """
        return q
        




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




