
"""Very Safe Python Expressions
"""
__rcs_id__='$Id: VSEval.py,v 1.12 1998/04/02 17:37:39 jim Exp $'

############################################################################
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  
#
############################################################################ 
__version__='$Revision: 1.12 $'[11:-2]

from string import join, find, split, translate
import sys, gparse, string

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

############################################################################
#
# $Log: VSEval.py,v $
# Revision 1.12  1998/04/02 17:37:39  jim
# Major redesign of block rendering. The code inside a block tag is
# compiled as a template but only the templates blocks are saved, and
# later rendered directly with render_blocks.
#
# Added with tag.
#
# Also, for the HTML syntax, we now allow spaces after # and after end
# or '/'.  So, the tags::
#
#   <!--#
#     with spam
#     -->
#
# and::
#
#   <!--#
#     end with
#     -->
#
# are valid.
#
# Revision 1.11  1998/03/12 21:37:01  jim
# Added _getattr.
#
# Revision 1.10  1998/03/10 17:30:41  jim
# Newlines (and carriage-returns are now allowed in expressions.
#
# Revision 1.9  1997/11/21 16:47:11  jim
# Got rid of non-needed and non-portable import of new.
#
# Revision 1.8  1997/11/11 18:13:49  jim
# updated expr machinery to use parse-tree manipulation
#
# Revision 1.7  1997/11/05 22:42:31  jim
# Changed careful_mul to be compatible with recent changes.
#
# Revision 1.6  1997/10/29 21:31:02  jim
# Changed namespace name to _vars.
#
# Revision 1.5  1997/10/29 17:00:11  jim
# Made namespace, __env__ public.
#
# Revision 1.4  1997/10/29 16:17:27  jim
# Added support for overriding getslice.
#
# Revision 1.3  1997/10/28 21:51:20  jim
# Removed validate attribute.
# Added template dict to override arguments.
#
# Revision 1.2  1997/10/27 17:40:35  jim
# Added some new experimental validation machinery.
# This is, still a work in progress.
#
# Revision 1.1  1997/09/22 14:41:13  jim
# Initial revision.
#
