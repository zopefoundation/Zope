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
__doc__='''Batch class, for iterating over a sequence in batches

$Id: Batch.py,v 1.3 2001/10/02 18:34:30 amos Exp $'''
__version__='$Revision: 1.3 $'[11:-2]

from ExtensionClass import Base

class LazyPrevBatch(Base):
    def __of__(self, parent):
        return Batch(parent._sequence, parent._size,
                     -1, parent.first + parent.overlap,
                     parent.orphan, parent.overlap)

class LazyNextBatch(Base):
    def __of__(self, parent):
        try: parent._sequence[parent.end]
        except IndexError: return None
        return Batch(parent._sequence, parent._size,
                     parent.end - parent.overlap, 0,
                     parent.orphan, parent.overlap)

class Batch(Base):
    """Create a sequence batch"""
    __allow_access_to_unprotected_subobjects__ = 1

    previous = LazyPrevBatch()
    next = LazyNextBatch()
    
    def __init__(self, sequence, size, start=0, end=0,
                 orphan=0, overlap=0):

        start = start + 1

        start,end,sz = opt(start,end,size,orphan,sequence)

        self._sequence = sequence
        self.size = sz
        self._size = size
        self.start = start
        self.end = end
        self.orphan = orphan
        self.overlap = overlap
        self.first = max(start - 1, 0)
        self.length = self.end - self.first
        if self.first == 0:
            self.previous = None
        
        
    def __getitem__(self, index):
        if index < 0:
            if index + self.end < self.first: raise IndexError, index
            return self._sequence[index + self.end]
        
        if index >= self.size: raise IndexError, index
        return self._sequence[index+self.first]

    def __len__(self):
        return self.length

def opt(start,end,size,orphan,sequence):
    if size < 1:
        if start > 0 and end > 0 and end >= start:
            size=end+1-start
        else: size=7

    if start > 0:

        try: sequence[start-1]
        except: start=len(sequence)

        if end > 0:
            if end < start: end=start
        else:
            end=start+size-1
            try: sequence[end+orphan-1]
            except: end=len(sequence)
    elif end > 0:
        try: sequence[end-1]
        except: end=len(sequence)
        start=end+1-size
        if start - 1 < orphan: start=1
    else:
        start=1
        end=start+size-1
        try: sequence[end+orphan-1]
        except: end=len(sequence)
    return start,end,size
