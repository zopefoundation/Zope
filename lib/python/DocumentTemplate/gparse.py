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
"$Id: gparse.py,v 1.7 1998/09/14 22:19:56 jim Exp $"
import sys, parser, symbol, token

from symbol import test, suite, argument, arith_expr, shift_expr
from symbol import subscriptlist, subscript, comparison, trailer, xor_expr
from symbol import term, not_test, factor, atom, expr, arglist
from symbol import power, and_test, and_expr

from token import STAR, NAME, RPAR, LPAR, NUMBER, DOT, STRING, COMMA
from token import ISTERMINAL, LSQB, COLON

from parser import sequence2ast, compileast, ast2list

ParseError='Expression Parse Error'

def munge(ast):
    if ISTERMINAL(ast[0]): return
    else:
        if ast[0]==term and len(ast) > 2:
            keep_going=1
            while keep_going:
                keep_going=0
                start=2
                for i in range(start,len(ast)-1):
                    if ast[i][0]==STAR:
                        ast[i-1:i+2]=[multi_munge(ast[i-1:i+2])]
                        keep_going=1
                        break
                        
            for a in ast[1:]: munge(a)

        elif ast[0]==power:
            keep_going=1
            while keep_going:
                keep_going=0
                start=2
                for i in range(start,len(ast)):
                    a=ast[i]
                    if a[0]==trailer:
                        if a[1][0]==DOT:
                            ast[:i+1]=dot_munge(ast,i)
                            keep_going=1
                            start=3
                            break
                        if a[1][0]==LSQB:
                            if (a[2][0] != subscriptlist or
                                a[2][1][0] != subscript):
                                raise ParseError, (
                                    'Unexpected form after left square brace')

                            slist=a[2]
                            if len(slist)==2:
                                # One subscript, check for range and ...
                                sub=slist[1]
                                if sub[1][0]==DOT:
                                    raise ParseError, (
                                        'ellipses are not supported')
                                l=len(sub)
                                if l < 3 and sub[1][0] != COLON:
                                    ast[:i+1]=item_munge(ast, i)
                                elif l < 5: ast[:i+1]=slice_munge(ast, i)
                                else: raise ParseError, 'Invalid slice'
                                    
                            else: ast[:i+1]=item_munge(ast, i)
                            keep_going=1
                            start=3
                            break

            for a in ast[1:]: munge(a)
        else:
            for a in ast[1:]: munge(a)
    return ast

def slice_munge(ast, i):
    # Munge a slice access into a function call
    # Note that we must account for a[:], a[b:], a[:b], and a[b:c]
    name=ast[i][2][1]
    args=[arglist]
    append=args.append

    a=(factor, (power, (atom, (NAME, '_vars'))))
    a=(argument, (test, (and_test, (not_test, (comparison,
       (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr,
       (term, a)))))))))))
    append(a)
    append([COMMA,','])

    a=ast[:i]
    a=(argument, (test, (and_test, (not_test, (comparison,
      (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
      (term, (factor, a))))))))))))
    append(a)

    sub=ast[i][2][1]
    l=len(sub)
    if sub[1][0]==COLON:
        if l==3:
            append([COMMA,','])
            a=(argument, (test, (and_test, (not_test, (comparison,
                (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
                (term, (factor, (power, (atom, (NUMBER, '0')))))))))))))))
            append(a)
            append([COMMA,','])
            append([argument, sub[2]])
    else:
        append([COMMA,','])
        append([argument, sub[1]])
        if l==4:
            append([COMMA,','])
            append([argument, sub[3]])

    return [power, [atom, [NAME, '__guarded_getslice__']],
                   [trailer, [LPAR, '('], args, [RPAR, ')'],
                    ]
            ]

def item_munge(ast, i):
    # Munge an item access into a function call
    name=ast[i][2][1]
    args=[arglist]
    append=args.append

    a=(factor, (power, (atom, (NAME, '_vars'))))
    a=(argument, (test, (and_test, (not_test, (comparison,
       (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
       (term, a)))))))))))
    append(a)
    append([COMMA,','])

    a=ast[:i]
    a=(argument, (test, (and_test, (not_test, (comparison,
      (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
      (term, (factor, a))))))))))))
    append(a)
    append([COMMA,','])

    for sub in ast[i][2][1:]:
        if sub[0]==COMMA: append(sub)
        else:
            if len(sub) != 2: raise ParseError, 'Invalid slice in subscript'
            append([argument, sub[1]])

    return [power, [atom, [NAME, '__guarded_getitem__']],
                   [trailer, [LPAR, '('], args, [RPAR, ')'],
                    ]
            ]

def dot_munge(ast, i):
    # Munge an attribute access into a function call
    name=ast[i][2][1]
    args=[arglist]
    append=args.append

    a=(factor, (power, (atom, (NAME, '_vars'))))
    a=(argument, (test, (and_test, (not_test, (comparison,
       (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
       (term, a)))))))))))
    append(a)
    append([COMMA,','])

    a=ast[:i]
    a=(argument, (test, (and_test, (not_test, (comparison,
      (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
      (term, (factor, a))))))))))))
    append(a)
    append([COMMA,','])

    a=(factor, (power, (atom, (STRING, `name`))))
    a=(argument, (test, (and_test, (not_test, (comparison,
       (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
       (term, a)))))))))))
    append(a)

    return [power, [atom, [NAME, '__guarded_getattr__']],
                   [trailer, [LPAR, '('], args, [RPAR, ')']],
            ]

def multi_munge(ast):
    # Munge a multiplication into a function call: __guarded_mul__
    args=[arglist]

    append=args.append
    a=(factor, (power, (atom, (NAME, '_vars'))))
    a=(argument, (test, (and_test, (not_test, (comparison,
       (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
       (term, a)))))))))))
    append(a)
    append([COMMA,','])

    for a in ast:
        if a[0]==STAR: args.append([COMMA,','])
        else:
            a=(argument, (test, (and_test, (not_test, (comparison,
               (expr, (xor_expr, (and_expr, (shift_expr, (arith_expr, 
               (term, a)))))))))))
            append(a)       

    return [factor, [power,
                     [atom, [NAME, '__guarded_mul__']],
                     [trailer, [LPAR, '('], args, [RPAR, ')'],
                      ]]]

def compile(src, file_name, ctype):
    if ctype=='eval': ast=parser.expr(src)
    elif ctype=='exec': ast=parser.suite(src)
    l=ast2list(ast)
    l=munge(l)
    ast=sequence2ast(l)
    return parser.compileast(ast, file_name)

