##############################################################################
#
# Copyright (c) 1998, Digital Creations, Fredericksburg, VA, USA.
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

"""Very Safe Python Expressions
"""
__rcs_id__='$Id: VSEval.py,v 1.17 1998/09/08 16:03:00 jim Exp $'
__version__='$Revision: 1.17 $'[11:-2]

from string import translate
import string
gparse=None

nltosp=string.maketrans('\r\n','  ')

def default_slicer(env, s, *ind):
    l=len(ind)
    if l==2: return s[ind[0]:ind[1]]
    elif l==1: return s[ind[0]:]
    return s[:]

def careful_mul(env, *factors):
    s=None
    r=1
    for factor in factors:
	try:
	    l=len(factor)
	    s=1
	except: l=factor
	if s and (l*r) > 1000: raise TypeError, 'Illegal sequence repeat'
	r=r*factor

    return r

default_globals={
    '__builtins__':{},
    '__guarded_mul__':       careful_mul,
    '__guarded_getattr__':   lambda env, inst, name: getattr(inst, name),
    '__guarded_getitem__':   lambda env, coll, key:  coll[key],
    '__guarded_getslice__':  default_slicer,
    }



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

    def __init__(self, expr, globals=default_globals):
	"""Create a 'safe' expression

	where:

  	  expr -- a string containing the expression to be evaluated.

	  globals -- A global namespace.
	"""
        global gparse
        if gparse is None: import gparse
        
	self.__name__=expr
	expr=translate(expr,nltosp)
	self.expr=expr
	self.globals=globals

	co=compile(expr,'<string>','eval')

	names=list(co.co_names)

	# Check for valid names, disallowing names that begin with '_' or
	# 'manage'. This is a DC specific rule and probably needs to be
	# made customizable!
	for name in names:
	    if name[:1]=='_' and name not in ('_', '_vars', '_getattr'):
		raise TypeError, 'illegal name used in expression'
		
	used={}

	i=0
	code=co.co_code
	l=len(code)
	LOAD_NAME=101	
	HAVE_ARGUMENT=90	
	def HAS_ARG(op): ((op) >= HAVE_ARGUMENT)
	while(i < l):
	    c=ord(code[i])
	    if c==LOAD_NAME:
		name=names[ord(code[i+1])+256*ord(code[i+2])]
		used[name]=1
		i=i+3		
	    elif c >= HAVE_ARGUMENT: i=i+3
	    else: i=i+1
	
	self.code=gparse.compile(expr,'<string>','eval')
	self.used=tuple(used.keys())

    def eval(self, mapping):
        d={'_vars': mapping}
	code=self.code
	globals=self.globals
	for name in self.used:
	    try: d[name]=mapping.getitem(name,0)
	    except KeyError:
		if name=='_getattr':
		    d['__builtins__']=globals
		    exec compiled_getattr in d

	return eval(code,globals,d)

    def __call__(self, **kw):
	return eval(self.code, self.globals, kw)

compiled_getattr=compile(
    'def _getattr(o,n): return __guarded_getattr__(_vars,o,n)',
    '<string>','exec')
