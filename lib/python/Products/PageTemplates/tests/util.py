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

######################################################################
# Utility facilities to aid setting things up.

import os, sys, string, re

from ExtensionClass import Base

class Bruce(Base):
    __allow_access_to_unprotected_subobjects__=1
    def __str__(self): return 'bruce'
    def __int__(self): return 42
    def __float__(self): return 42.0
    def keys(self): return ['bruce']*7
    def values(self): return [self]*7
    def items(self): return [('bruce',self)]*7
    def __len__(self): return 7
    def __getitem__(self,index):
        if (type(index) is type(1) and 
            (index < 0 or index > 6)): raise IndexError, index
        return self
    isDocTemp=0
    def __getattr__(self,name):
        if name[:1]=='_': raise AttributeError, name
        return self
   
bruce=Bruce()    

class arg(Base):
    __allow_access_to_unprotected_subobjects__=1
    def __init__(self,nn,aa): self.num, self.arg = nn, aa
    def __str__(self): return str(self.arg)

class argv(Base):
    __allow_access_to_unprotected_subobjects__=1
    def __init__(self, argv=sys.argv[1:]):
        args=self.args=[]
        for aa in argv:
            args.append(arg(len(args)+1,aa))

    def items(self):
        return map(lambda a: ('spam%d' % a.num, a), self.args)

    def values(self): return self.args

    def getPhysicalRoot(self):
        return self

def nicerange(lo, hi):
    if hi <= lo+1:
        return str(lo+1)
    else:
        return "%d,%d" % (lo+1, hi)

def check_html(s1, s2):
    s1 = normalize_html(s1)
    s2 = normalize_html(s2)
    if s1!=s2:
        print
        from OFS.ndiff import SequenceMatcher, dump, IS_LINE_JUNK
        a = string.split(s1, '\n')
        b = string.split(s2, '\n')
        def add_nl(s):
            return s + '\n'
        a = map(add_nl, a)
        b = map(add_nl, b)
        cruncher=SequenceMatcher(isjunk=IS_LINE_JUNK, a=a, b=b)
        for tag, alo, ahi, blo, bhi in cruncher.get_opcodes():
            if tag == 'equal':
                continue
            print nicerange(alo, ahi) + tag[0] + nicerange(blo, bhi)
            dump('<', a, alo, ahi)
            if a and b:
                print '---'
            dump('>', b, blo, bhi)
    assert s1==s2, "HTML Output Changed"

def check_xml(s1, s2):
    s1 = normalize_xml(s1)
    s2 = normalize_xml(s2)
    assert s1==s2, "XML Output Changed"

def normalize_html(s):
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"/>", ">", s)
    return s

def normalize_xml(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(?s)\s+<", "<", s)
    s = re.sub(r"(?s)>\s+", ">", s)
    return s


import Products.PageTemplates.tests
dir = os.path.dirname( Products.PageTemplates.tests.__file__)
input_dir = os.path.join(dir, 'input')
output_dir = os.path.join(dir, 'output')

def read_input(filename):
    filename = os.path.join(input_dir, filename)
    return open(filename, 'r').read()

def read_output(filename):
    filename = os.path.join(output_dir, filename)
    return open(filename, 'r').read()
