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

from Lexicon import Lexicon


__doc__=""" Lexicon object that supports 

"""

from Splitter import Splitter
from Persistence import Persistent
from Acquisition import Implicit
import OIBTree, BTree, IOBTree
from intSet import intSet
OIBTree=OIBTree.BTree
OOBTree=BTree.BTree
IOBTree=IOBTree.BTree
import re

from UnTextIndex import Or

class GlobbingLexicon(Lexicon):
    """

    Base class to support globbing lexicon object.
    """

    multi_wc = '*'
    single_wc = '?'
    eow = '$'

    def __init__(self):

        self.counter = 0
        self._lexicon = OIBTree()
        self._inverseLex = IOBTree()
        self._digrams = OOBTree()

    def set(self, word):
        """  """

        if self._lexicon.has_key(word):
            return self._lexicon[word]

        else:
            word = intern(word)
            self._lexicon[word] = self.counter
            self._inverseLex[self.counter] = word

            ## now, split the word into digrams and insert references
            ## to 'word' into the digram object.  The first and last
            ## digrams in the list are specially marked with $ to
            ## indicate the beginning and end of the word

            digrams = []
            digrams.append(self.eow + word[0]) # mark the beginning

            for i in range(len(word)):
                digrams.append(word[i:i+2])

            digrams[-1] = digrams[-1] + self.eow  # mark the end

            _digrams = self._digrams
            
            for digram in digrams:
                set = _digrams.get(digram)
                if set is None:
                    _digrams[digram] = set = intSet()
                    
                set.insert(self.counter)

            self._digrams = _digrams
            
            self.counter = self.counter + 1
            return self.counter


    def get(self, pattern):
        """ Query the lexicon for words matching a pattern.

        """

        wc_set = [self.multi_wc, self.single_wc]
        digrams = []
        for i in range(len(pattern)):

            if pattern[i] in wc_set:
                continue

            if i == 0:
                digrams.insert(i, (self.eow + pattern[i]) )
                digrams.append((pattern[i] + pattern[i+1]))
            else:
                try:
                    if pattern[i+1] not in wc_set:
                        digrams.append( pattern[i] + pattern[i+1] )

                except IndexError:
                    digrams.append( (pattern[i] + self.eow) )



        ## now get all of the intsets that contain the result digrams

        result = None
        for digram in digrams:
            if self._digrams.has_key(digram):
                set = self._digrams[digram]
                if set is not None:
                    if result is None:
                        result = set
                    else:
                        result.intersection(set)

        if result is None:
            return ()
        else:
            ## now we have narrowed the list of possible candidates
            ## down to those words which contain digrams.  However,
            ## some words may have been returned that match digrams,
            ## but do not match 'pattern'.  This is because some words
            ## may contain all matching digrams, but in the wrong
            ## order.

            expr = re.compile(self.translate(pattern))
            words = []
            hits = []
            for x in result:
                if expr.search(self._inverseLex[x]):
                    hits.append(x)

            return hits
                
    def __getitem__(self, word):
        """ """
        return self.get(word)

    def query_hook(self, q):
        """expand wildcards

        """
        words = []
        for w in q:
            if ( (self.multi_wc in w) or
                (self.single_wc in w) ):
                wids = self.get(w)
                for wid in wids:
                    if words:
                        words.append(Or)
                    words.append(self._inverseLex[wid])
            else:
                words.append(w)

        return words

    def Splitter(self, astring, words=None):
        """ wrap the splitter """

        ## don't do anything, less efficient but there's not much
        ## sense in stemming a globbing lexicon.

        return Splitter(astring)


    def translate(self, pat):
        """Translate a PATTERN to a regular expression.

        There is no way to quote meta-characters.
        """

        i, n = 0, len(pat)
        res = ''
        while i < n:
            c = pat[i]
            i = i+1
            if c == self.multi_wc:
                res = res + '.*'
            elif c == self.single_wc:
                res = res + '.'
            else:
                res = res + re.escape(c)
        return res + "$"












