
"""Very Safe Python Expressions
"""
__rcs_id__='$Id: VSEval.py,v 1.1 1997/09/22 14:41:13 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
############################################################################ 
__version__='$Revision: 1.1 $'[11:-2]

from string import join
import new, sys

class Eval:
    """Provide a very-safe environment for evaluating expressions

    This class lets you overide operations, __power__, __mul__,
    __div__, __mod__, __add__, __sub__, __getitem__, __lshift__,
    __rshift__, __and__, __xor__, __or__,__pos__, __neg__, __not__,
    __repr__, __invert__, and __getattr__.

    For example, __mult__ might be overridden to prevent expressions like::

      'I like spam' * 100000000

    or to disallow or limit attribute access.

    """

    def __init__(self, expr, custom=None, globals={'__builtins__':{}}, **kw):
	"""Create a 'safe' expression

	where:

  	  expr -- a string containing the expression to be evaluated.

	  custom -- a mapping from operation names to:

	    - None, meaning that the operation is not allowed, or

	    - a callable object to be called in place of the operation.

	  globals -- A global namespace.
	"""

	if custom:
	    if kw:
		d={}
		for k, v in custom.items(): d[k]=v
		for k, v in kw.items(): d[k]=v
		custom=d
	else: custom=kw

	self.expr=expr
	self.globals=globals

	co=compile(expr,'<string>','eval')

	out=[]
	names=list(co.co_names)
	consts=list(co.co_consts)
	used={}

	i=0
	code=co.co_code
	l=len(code)
	while(i < l):
	    c=ord(code[i])
	    if binops.has_key(c) and custom.has_key(binops[c]):
		name=binops[c]
		custop=custom[name]
		if custop==None:
		    raise TypeError, ("illegal operation, %s, in %s"
				      % (name, expr))

		self._const(out, custop, consts)
		self._bfunc(out)
		i=i+1

	    elif unops.has_key(c) and custom.has_key(unops[c]):
		name=unops[c]
		custop=custom[name]
		if custop==None:
		    raise TypeError, ("illegal operation, %s, in %s"
				      % (name, expr))

		self._const(out, custop, consts)
		self._ufunc(out)
		i=i+1

	    elif c==LOAD_ATTR and custom.has_key('__getattr__'):
		name='__getattr__'
		custop=custom[name]
		if custop==None:
		    raise TypeError, (
			"""Attempt tp perform attribute access in "%s".
			Attribute access is not allowed.
			"""
			% expr)
		
		self._const(out, names[ord(code[i+1])+256*ord(code[i+2])],
			    consts)
		self._const(out, custop, consts)
		self._bfunc(out)
		i=i+3

	    elif c==LOAD_NAME:
		out.append(c)
		out.append(ord(code[i+1]))
		out.append(ord(code[i+2]))
		name=names[256*out[-1]+out[-2]]
		used[name]=1
		i=i+3
		
	    else:
		out.append(c)
		i=i+1
		if HAS_ARG(c):
		    out.append(ord(code[i]))
		    out.append(ord(code[i+1]))
		    i=i+2

	code=join(map(chr,out),'')
	code=new.code(
	    co.co_argcount, co.co_nlocals, co.co_flags, code, tuple(consts),
	    tuple(names), co.co_varnames, co.co_filename, co.co_name)

	self.code=code
	self.used=tuple(used.keys())

    def _const(self, out, v, consts):
	# Load object as a constant
	try: i=consts.index(v)
	except:
	    i=len(consts)
	    consts.append(v)
	out.append(LOAD_CONST)
	out.append(i%256)
	out.append(i/256)

    def _bfunc(self, out): 
	out.append(ROT_THREE)
	out.append(CALL_FUNCTION)
	out.append(2)
	out.append(0)

    def _ufunc(self, out): 
	out.append(ROT_TWO)
	out.append(CALL_FUNCTION)
	out.append(1)
	out.append(0)

    def eval(self, mapping):
	d={}
	code=self.code
	for name in self.used:
	    try: d[name]=mapping[name]
	    except: pass

	return eval(code,self.globals,d)

    def __call__(self, **kw):
	return eval(self.code, self.globals, kw)

def co(e,t='eval'):
    """Utility to show code object meta data.

    Just call co('some expression')

    The byte codes are shown as a list of integers.
    """

    c=compile(e,'<string>', t)
    print '__members__', c.__members__
    print '\targcount', c.co_argcount
    print '\tcode', map(ord,c.co_code)
    print '\tconsts', c.co_consts
    print '\tvarnames', c.co_varnames
    print '\tflags', c.co_flags
    print '\tnames', c.co_names
    print '\tnlocals', c.co_nlocals

############################################################################
# Operator/Bytecode data.  This has to change when the VM changes.    
    
POP_TOP=	1
ROT_TWO=	2
ROT_THREE=3
DUP_TOP=	4
UNARY_POSITIVE=10
UNARY_NEGATIVE=11
UNARY_NOT=12
UNARY_CONVERT=13
UNARY_INVERT=15
BINARY_POWER=19
BINARY_MULTIPLY=20
BINARY_DIVIDE=21
BINARY_MODULO=22
BINARY_ADD=23
BINARY_SUBTRACT=24
BINARY_SUBSCR=25
SLICE=	30
STORE_SLICE=40
DELETE_SLICE=50
STORE_SUBSCR=60
DELETE_SUBSCR=61
BINARY_LSHIFT=62
BINARY_RSHIFT=63
BINARY_AND=64
BINARY_XOR=65
BINARY_OR=66
PRINT_EXPR=70
PRINT_ITEM=71
PRINT_NEWLINE=72
BREAK_LOOP=80
LOAD_LOCALS=82
RETURN_VALUE=83
EXEC_STMT=85
POP_BLOCK=87
END_FINALLY=88
BUILD_CLASS=89
STORE_NAME=90	
DELETE_NAME=91	
UNPACK_TUPLE=92	
UNPACK_LIST=93	
UNPACK_ARG=94	
STORE_ATTR=95	
DELETE_ATTR=96	
STORE_GLOBAL=97	
DELETE_GLOBAL=98	
UNPACK_VARARG=99	
LOAD_CONST=100	
LOAD_NAME=101	
BUILD_TUPLE=102	
BUILD_LIST=103	
BUILD_MAP=104	
LOAD_ATTR=105	
COMPARE_OP=106	
IMPORT_NAME=107	
IMPORT_FROM=108	
ACCESS_MODE=109	
JUMP_FORWARD=110	
JUMP_IF_FALSE=111	
JUMP_IF_TRUE=112	
JUMP_ABSOLUTE=113	
FOR_LOOP=114	
LOAD_LOCAL=115	
LOAD_GLOBAL=116
SET_FUNC_ARGS=117
SETUP_LOOP=120
SETUP_EXCEPT=121
SETUP_FINALLY=122
LOAD_FAST=124
STORE_FAST=125
DELETE_FAST=126
SET_LINENO=127
RAISE_VARARGS=130
CALL_FUNCTION=131
MAKE_FUNCTION=132
BUILD_SLICE =133

STOP_CODE=0
HAVE_ARGUMENT=90	
def HAS_ARG(op): ((op) >= HAVE_ARGUMENT)

unops={
    UNARY_POSITIVE: '__pos__',
    UNARY_NEGATIVE: '__neg__',
    UNARY_NOT: '__not__',
    UNARY_CONVERT: '__repr__',
    UNARY_INVERT: '__invert__',
    }

binops={
    BINARY_POWER: '__power__',
    BINARY_MULTIPLY: '__mul__',
    BINARY_DIVIDE: '__div__',
    BINARY_MODULO: '__mod__',
    BINARY_ADD: '__add__',
    BINARY_SUBTRACT: '__sub__',
    BINARY_SUBSCR: '__getitem__',
    BINARY_LSHIFT: '__lshift__',
    BINARY_RSHIFT: '__rshift__',
    BINARY_AND: '__and__',
    BINARY_XOR: '__xor__',
    BINARY_OR: '__or__',
    }

############################################################################
#
# Testing code:

def mul(x,y):
    print "mul(%s,%s)" % (x,y)
    return x*y

def attr(x,y):
    print "attr(%s,%s)" % (x,y)
    return getattr(x,y)

class A: b="A.b"

def t1():
    e=Eval('a*b', __mul__=mul, __getattr__=attr)
    print e(a=2, b=3)

def t2():
    e=Eval('a.b', __mul__=mul, __getattr__=attr)
    print e(a=A)

def t3():
    e=Eval('a.b', __mul__=mul, __getattr__=None)
    print e(a=A)

def careful_mul(a,b):
    try: l1=len(a)
    except: l1=a
    try: l2=len(b)
    except: l2=b
    if l1*l2 > 1000: raise TypeError, 'Illegal sequence repeat'
    return a*b

"""Notes

What can mess us up?

  - Creating very large sequences through mult

  - Creating very large sequences through map:
     map(lambda i:
         map(lambda i:
             map(lambda i: 'spam',
                 range(1000)),
             range(1000)),
         range(1000))

  - range(1000000000)

  Maybe provide limited range? Or no range at all?

  Maybe no map? Remember that map is a kind of for loop.
"""

if __name__=='__main__': globals()[sys.argv[1]]()

############################################################################
#
# $Log: VSEval.py,v $
# Revision 1.1  1997/09/22 14:41:13  jim
# Initial revision.
#
