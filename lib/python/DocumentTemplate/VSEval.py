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
"""Very Safe Python Expressions
"""
__rcs_id__='$Id: VSEval.py,v 1.23 1999/10/28 18:02:41 brian Exp $'
__version__='$Revision: 1.23 $'[11:-2]

from string import translate, strip
import string
gparse=None

nltosp=string.maketrans('\r\n','  ')

def default_slicer(env, s, *ind):
    l=len(ind)
    if l==2: return s[ind[0]:ind[1]]
    elif l==1: return s[ind[0]:]
    return s[:]

def careful_mul(env, *factors):
    # r = result (product of all factors)
    # c = count (product of all non-sequence factors)
    # s flags whether any of the factors is a sequence
    r=c=1
    s=None
    for factor in factors:
        try:
            l=len(factor)
            s=1
        except TypeError:
            c=c*factor
        if s and c > 1000:
            raise TypeError, \
                  'Illegal sequence repeat (too many repetitions: %d)' % c
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

        expr=strip(expr)
        
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
