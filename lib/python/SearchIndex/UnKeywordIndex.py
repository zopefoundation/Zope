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

from UnIndex import UnIndex, MV, intSet
from zLOG import LOG, ERROR
from Missing import MV
from types import *

class UnKeywordIndex(UnIndex):

    meta_type = 'Keyword Index'
    
    """Like an UnIndex only it indexes sequences of items
    
    Searches match any keyword.

    This should have an _apply_index that returns a relevance score
    """

    def index_object(self, documentId, obj, threshold=None):
        """ index an object 'obj' with integer id 'i'

        Ideally, we've been passed a sequence of some sort that we
        can iterate over. If however, we haven't, we should do something
        useful with the results. In the case of a string, this means
        indexing the entire string as a keyword."""

        # First we need to see if there's anything interesting to look at
        # self.id is the name of the index, which is also the name of the
        # attribute we're interested in.  If the attribute is callable,
        # we'll do so.
        try:
            newKeywords = getattr(obj, self.id)
            if callable(newKeywords):
                newKeywords = newKeywords()
        except AttributeError:
            newKeywords = MV

        if type(newKeywords) is StringType:
            newKeywords = (newKeywords, )

        # Now comes the fun part, we need to figure out what's changed
        # if anything from the previous record.
        oldKeywords = self._unindex.get(documentId, MV)

        if newKeywords is MV:
            self.unindex_object(documentId)
            return 0
        elif oldKeywords is MV:
            try:
                for kw in newKeywords:
                    self.insertForwardIndexEntry(kw, documentId)
            except TypeError:
                return 0
        else:
            # We need the old keywords to be a mapping so we can manipulate
            # them more easily.
            tmp = {}
            try:
                for kw in oldKeywords:
                    tmp[kw] = None
                    oldKeywords = tmp

                    # Now we're going to go through the new keywords,
                    # and add those that aren't already indexed.  If
                    # they are already indexed, just delete them from
                    # the list.
                    for kw in newKeywords:
                        if oldKeywords.has_key(kw):
                            del oldKeywords[kw]
                        else:
                            self.insertForwardIndexEntry(kw, documentId)

                    # Now whatever is left in oldKeywords are keywords
                    # that we no longer have, and need to be removed
                    # from the indexes.
                    for kw in oldKeywords.keys():
                        self.removeForwardIndexEntry(kw, documentId)

            except TypeError:
                return 0
        
        self._unindex[documentId] = newKeywords[:] # Make a copy

        return 1
    

    def unindex_object(self, documentId):
        """ carefully unindex the object with integer id 'documentId'"""

        keywords = self._unindex.get(documentId, MV)
        if keywords is MV:
            return None
        for kw in keywords:
            self.removeForwardIndexEntry(kw, documentId)

        del self._unindex[documentId]
