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
"$Id: gparse_test.py,v 1.3 1999/03/10 00:15:08 klm Exp $"
import sys, parser, symbol, token
from symbol import *
from token import *
from parser import sequence2ast, compileast, ast2list
from gparse import *

def pretty(s):
    l=ast2list(parser.expr(s))
    print l
    pret(l)

def astl(s): return parser.ast2list(parser.expr(s))

def pret(ast, level=0):
    if ISTERMINAL(ast[0]): print '  '*level, ast[1]
    else:
        print '  '*level, sym_name[ast[0]], '(%s)' % ast[0]
        for a in ast[1:]:
            pret(a,level+1)
    
def tpretty():
    print 60*'='
    for arg in sys.argv[1:]:
      print
      print arg
      pretty(arg)
      print 60*'='

def check(expr1=None, expr2=None):
    ok=1
    expr1=expr1 or sys.argv[1]
    expr2=expr2 or sys.argv[2]
    l1=munge(astl(expr1))
    l2=astl(expr2)
    try: c1=compileast(sequence2ast(l1))
    except:
        traceback.print_exc
        c1=None
    c2=compileast(sequence2ast(l2))
    if c1 !=c2:
        ok=0
        print 'test failed', expr1, expr2
        print
        print l1
        print
        print l2
        print

    ast=parser.sequence2ast(l1)
    c=parser.compileast(ast)

    pretty(expr1)
    pret(l1)
    pret(l2)

    return ok
    
def spam():
    # Regression test
    import traceback
    ok=1
    for expr1, expr2 in (
        ("a*b",         "__guarded_mul__(_vars, a, b)"),
        ("a*b*c",
         "__guarded_mul__(_vars, __guarded_mul__(_vars, a, b), c)"
         ),
        ("a.b",         "__guarded_getattr__(_vars, a, 'b')"),
        ("a[b]",        "__guarded_getitem__(_vars, a, b)"),
        ("a[b,c]",      "__guarded_getitem__(_vars, a, b, c)"),
        ("a[b:c]",      "__guarded_getslice__(_vars, a, b, c)"),
        ("a[:c]",       "__guarded_getslice__(_vars, a, 0, c)"),
        ("a[b:]",       "__guarded_getslice__(_vars, a, b)"),
        ("a[:]",        "__guarded_getslice__(_vars, a)"),
        ("_vars['sequence-index'] % 2",
         "__guarded_getitem__(_vars, _vars, 'sequence-index') % 2"
         ),
        ):
        l1=munge(astl(expr1))
        l2=astl(expr2)
        try: c1=compileast(sequence2ast(l1))
        except:
            traceback.print_exc
            c1=None
        c2=compileast(sequence2ast(l2))
        if c1 !=c2:
            ok=0
            print 'test failed', expr1, expr2
            print
            print l1
            print
            print l2
            print

        ast=parser.sequence2ast(l1)
        c=parser.compileast(ast)
        
    if ok: print 'all tests succeeded'

if __name__=='__main__':
    try:
        c=sys.argv[1]
        del sys.argv[1]
        globals()[c]()
    except: spam()    

