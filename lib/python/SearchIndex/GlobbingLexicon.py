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
from intSet import intSet
from UnTextIndex import Or

import re, string
import OIBTree, BTree, IOBTree, IIBTree

# Short cuts for common data containers
OIBTree = OIBTree.BTree                 # Object -> Integer
OOBTree = BTree.BTree                   # Object -> Object
IOBTree = IOBTree.BTree                 # Integer -> Object
IIBucket = IIBTree.Bucket               # Integer -> Integer


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
        self.counter = 0                # word id counter XXX
        self._lexicon = OIBTree()
        self._inverseLex = IOBTree()
        self._digrams = OOBTree()


    def createDigrams(self, word):
        """Returns a list with the set of digrams in the word."""
        digrams = []

        digrams.append(self.eow + word[0])    # Mark the beginning

        for i in range(len(word)):
            digrams.append(word[i:i+2])

        digrams[-1] = digrams[-1] + self.eow  # Mark the end

        return digrams

    
    def getWordId(self, word):
        """Provided 'word', return the matching integer word id."""

        if self._lexicon.has_key(word):
            return self._lexicon[word]
        else:
            return self.assignWordId(word)

    set = getWordId                     # Kludge for old code


    def assignWordId(self, word):
        """Assigns a new word id to the provided word, and return it."""

        # Double check it's not in the lexicon already, and if it is, just
        # return it.
        if self._lexicon.has_key(word):
            return self._lexicon[word]
        
        # First we go ahead and put the forward and reverse maps in.
        self._lexicon[word] = self.counter
        self._inverseLex[self.counter] = word

        # Now take all the digrams and insert them into the digram map.
        for digram in self.createDigrams(word):
            set = self._digrams.get(digram)
            if set is None:
                self._digrams[digram] = set = intSet()
            set.insert(self.counter)

        self.counter = self.counter + 1
        return self.counter - 1         # Adjust for the previous increment

    
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
            result =  self._lexicon.get(pattern, ())
            return (result, )
        
        ## now get all of the intsets that contain the result digrams
        result = IIBucket()
        for digram in digrams:
            if self._digrams.has_key(digram):
                matchSet = self._digrams[digram]
                if matchSet is not None:
                    result = IIBucket().union(matchSet)

        if len(result) == 0:
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
            hits = []
            for x in result.keys():
                if expr.match(self._inverseLex[x]):
                    hits.append(x)
            return hits

                
    def __getitem__(self, word):
        """ """
        return self.get(word)


    def query_hook(self, q):
        """expand wildcards"""
        words = []
        wids = []
        for w in q:
            if ( (self.multi_wc in w) or
                 (self.single_wc in w) ):
                wids = self.get(w)
                for wid in wids:
                    if words:
                        words.append(Or)
                    words.append(wid)
            else:
                words.append(w)

        return words


    def Splitter(self, astring, words=None):
        """ wrap the splitter """

        ## don't do anything, less efficient but there's not much
        ## sense in stemming a globbing lexicon.

        return Splitter(astring)


    def createRegex(self, pat):
        """Translate a PATTERN to a regular expression.

        There is no way to quote meta-characters.
        """

        transTable = string.maketrans("", "")
        
        # First, deal with mutli-character globbing
        result = string.replace(pat, '*', '.*')

        # Next, we need to deal with single-character globbing
        result = string.replace(result, '?', '.?')

        # Now, we need to remove all of the characters that
        # are forbidden.
        result = string.translate(result, transTable,
                                  r'()&|!@#$%^{}\<>')

        return "%s$" % result 
