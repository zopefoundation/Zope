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


class ResultList:
  
    def __init__(self, d, words, index, TupleType=type(())):
        self._index = index
        self._words = words
        if (type(d) is TupleType): self._dict = { d[0] : d[1] }
        else: self._dict = d
    
    def __len__(self): return len(self._dict)

    def __getitem__(self, key): return self._dict[key]

    def keys(self): return self._dict.keys()

    def has_key(self, key): return self._dict.has_key(key)

    def items(self): return self._dict.items()  

    def __and__(self, x):
        result = {}
        dict = self._dict
        xdict = x._dict
        xhas = xdict.has_key
        for id, score in dict.items():
            if xhas(id): result[id] = xdict[id]+score
    
        return self.__class__(result, self._words+x._words, self._index)

    def and_not(self, x):
        result = {}
        dict = self._dict
        xdict = x._dict
        xhas = xdict.has_key
        for id, score in dict.items():
            if not xhas(id): result[id] = xdict[id]+score
    
        return self.__class__(result, self._words, self._index)
  
    def __or__(self, x):
        result = {}
        dict = self._dict
        has = dict.has_key
        xdict = x._dict
        xhas = xdict.has_key
        for id, score in dict.items():
            if xhas(id): result[id] = xdict[id]+score
            else: result[id] = score

        for id, score in xdict.items():
            if not has(id): result[id] = score
    
        return self.__class__(result, self._words+x._words, self._index)

    def near(self, x):
        result = {}
        dict = self._dict
        xdict = x._dict
        xhas = xdict.has_key
        positions = self._index.positions
        for id, score in dict.items():
            if not xhas(id): continue
            p=(map(lambda i: (i,0), positions(id,self._words))+
               map(lambda i: (i,1), positions(id,x._words)))
            p.sort()
            d = lp = 9999
            li = None
            lsrc = None
            for i,src in p:
                if i is not li and src is not lsrc and li is not None:
                    d = min(d,i-li)
                li = i
                lsrc = src
            if d==lp: score = min(score,xdict[id]) # synonyms
            else: score = (score+xdict[id])/d
            result[id] = score
    
        return self.__class__(result, self._words+x._words, self._index)

