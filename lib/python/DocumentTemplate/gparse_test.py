##############################################################################
#
# Copyright (c) 1996-1998, Digital Creations, Fredericksburg, VA, USA.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
# 
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
# 
#       This product includes software developed by Digital Creations
#       and its contributors.
# 
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS IS*
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
# CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
#
# 
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
#
##############################################################################
"$Id: gparse_test.py,v 1.1 1998/09/14 21:10:07 jim Exp $"
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
	("a*b", 	"__guarded_mul__(_vars, a, b)"),
	("a*b*c",
	 "__guarded_mul__(_vars, __guarded_mul__(_vars, a, b), c)"
	 ),
	("a.b",		"__guarded_getattr__(_vars, a, 'b')"),
	("a[b]", 	"__guarded_getitem__(_vars, a, b)"),
	("a[b,c]", 	"__guarded_getitem__(_vars, a, b, c)"),
	("a[b:c]",	"__guarded_getslice__(_vars, a, b, c)"),
	("a[:c]",	"__guarded_getslice__(_vars, a, 0, c)"),
	("a[b:]",	"__guarded_getslice__(_vars, a, b)"),
	("a[:]",	"__guarded_getslice__(_vars, a)"),
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

