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
#############################################################################

from Lexicon import Lexicon
from Splitter import Splitter
from UnTextIndex import Or

import re, string

from BTrees.IIBTree import IISet, union, IITreeSet
from BTrees.OIBTree import OIBTree
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from randid import randid

class GlobbingLexicon(Lexicon):
    """Lexicon which supports basic globbing function ('*' and '?').

    This lexicon keeps several data structures around that are useful
    for searching. They are:

      '_lexicon' -- Contains the mapping from word => word_id

      '_inverseLex' -- Contains the mapping from word_id => word

      '_digrams' -- Contains a mapping from digram => word_id

    Before going further, it is necessary to understand what a digram is,
    as it is a core component of the structure of this lexicon.  A digram
    is a two-letter sequence in a word.  For example, the word 'zope'
    would be converted into the digrams::

      ['$z', 'zo', 'op', 'pe', 'e$']

    where the '$' is a word marker.  It is used at the beginning and end
    of the words.  Those digrams are significant.
    """

    multi_wc = '*'
    single_wc = '?'
    eow = '$'


    def __init__(self):
        self.clear()

    def clear(self):
        self._lexicon = OIBTree()
        self._inverseLex = IOBTree()
        self._digrams = OOBTree()

    def _convertBTrees(self, threshold=200):
        Lexicon._convertBTrees(self, threshold)
        if type(self._digrams) is OOBTree: return

        from BTrees.convert import convert

        _digrams=self._digrams
        self._digrams=OOBTree()
        self._digrams._p_jar=self._p_jar
        convert(_digrams, self._digrams, threshold, IITreeSet)


    def createDigrams(self, word):
        """Returns a list with the set of digrams in the word."""
        digrams = list(word)
        digrams.append(self.eow)
        last = self.eow

        for i in range(len(digrams)):
            last, digrams[i] = digrams[i], last + digrams[i]

        return digrams

    
    def getWordId(self, word):
        """Provided 'word', return the matching integer word id."""

        if self._lexicon.has_key(word):
            return self._lexicon[word]
        else:
            return self.assignWordId(word)

    set = getWordId                     # Kludge for old code

    def getWord(self, wid):
        return self._inverseLex.get(wid, None)

    def assignWordId(self, word):
        """Assigns a new word id to the provided word, and return it."""

        # Double check it's not in the lexicon already, and if it is, just
        # return it.
        if self._lexicon.has_key(word):
            return self._lexicon[word]


        # Get word id. BBB Backward compat pain.
        inverse=self._inverseLex
        try: insert=inverse.insert
        except AttributeError:
            # we have an "old" BTree object
            if inverse:            
                wid=inverse.keys()[-1]+1
            else:
                self._inverseLex=IOBTree()
                wid=1
            inverse[wid] = word
        else:
            # we have a "new" IOBTree object
            wid=randid()
            while not inverse.insert(wid, word):
                wid=randid()

        self._lexicon[word] = wid

        # Now take all the digrams and insert them into the digram map.
        for digram in self.createDigrams(word):
            set = self._digrams.get(digram, None)
            if set is None:
                self._digrams[digram] = set = IISet()
            set.insert(wid)

        return wid

    
    def get(self, pattern):
        """ Query the lexicon for words matching a pattern."""
        wc_set = [self.multi_wc, self.single_wc]

        digrams = []
        globbing = 0
        for i in range(len(pattern)):
            if pattern[i] in wc_set:
                globbing = 1
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

        if not globbing:
            result =  self._lexicon.get(pattern, None)
            if result is None:
                return ()
            return (result, )
        
        ## now get all of the intsets that contain the result digrams
        result = None
        for digram in digrams:
            result=union(result, self._digrams.get(digram, None))

        if not result:
            return ()
        else:
            ## now we have narrowed the list of possible candidates
            ## down to those words which contain digrams.  However,
            ## some words may have been returned that match digrams,
            ## but do not match 'pattern'.  This is because some words
            ## may contain all matching digrams, but in the wrong
            ## order.

            expr = re.compile(self.createRegex(pattern))
            words = []
            hits = IISet()
            for x in result:
                if expr.match(self._inverseLex[x]):
                    hits.insert(x)
            return hits

                
    def __getitem__(self, word):
        """ """
        return self.get(word)


    def query_hook(self, q):
        """expand wildcards"""
        ListType = type([])
        i = len(q) - 1
        while i >= 0:
            e = q[i]
            if isinstance(e, ListType):
                self.query_hook(e)
            elif ( (self.multi_wc in e) or
                   (self.single_wc in e) ):
                wids = self.get(e)
                words = []
                for wid in wids:
                    if words:
                        words.append(Or)
                    words.append(wid)
                if not words:
                    # if words is empty, return something that will make
                    # textindex's __getitem__ return an empty result list
                    words.append('')
                q[i] = words
            i = i - 1

        return q

    def Splitter(self, astring, words=None):
        """ wrap the splitter """

        ## don't do anything, less efficient but there's not much
        ## sense in stemming a globbing lexicon.

        return Splitter(astring)


    def createRegex(self, pat):
        """Translate a PATTERN to a regular expression.

        There is no way to quote meta-characters.
        """

        # Remove characters that are meaningful in a regex
        transTable = string.maketrans("", "")
        result = string.translate(pat, transTable,
                                  r'()&|!@#$%^{}\<>.')
        
        # First, deal with multi-character globbing
        result = string.replace(result, '*', '.*')

        # Next, we need to deal with single-character globbing
        result = string.replace(result, '?', '.')

        return "%s$" % result 

