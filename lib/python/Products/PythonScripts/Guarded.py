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

__version__='$Revision: 1.4 $'[11:-2]

from zbytecodehacks.VSExec import SafeBlock, GuardedBinaryOps, \
     UntupleFunction, RedirectWrites, WriteGuard, RedirectReads, ReadGuard, \
     LoopLimits, bind
from DocumentTemplate.VSEval import careful_mul
from DocumentTemplate.DT_Util import TemplateDict, \
     careful_pow, d, ValidationError
from DocumentTemplate.DT_Var import special_formats
from AccessControl import getSecurityManager
try:
    from AccessControl import secureModule
except:
    # Allow pre-2.3 Zopes to operate without import capability
    def secureModule(*args):
        return

safefuncs = TemplateDict()
safebin = {}
for name in ('None', 'abs', 'chr', 'divmod', 'float', 'hash', 'hex', 'int',
             'len', 'max', 'min', 'oct', 'ord', 'round', 'str'):
    safebin[name] = d[name]
for name in ('range', 'pow', 'DateTime', 'test', 'namespace', 'render'):
    safebin[name] = getattr(safefuncs, name)

for name in ('ArithmeticError', 'AttributeError', 'EOFError',
             'EnvironmentError', 'FloatingPointError', 'IOError',
             'ImportError', 'IndexError', 'KeyError',
             'LookupError', 'NameError', 'OSError', 'OverflowError',
             'RuntimeError', 'StandardError', 'SyntaxError',
             'TypeError', 'ValueError', 'ZeroDivisionError',
             'apply', 'callable', 'cmp', 'complex', 'isinstance',
             'issubclass', 'long', 'repr'):
    safebin[name] = __builtins__[name]

def same_type(arg1, *args):
    '''Compares the type of two or more objects.'''
    base = getattr(arg1, 'aq_base', arg1)
    t = type(base)
    for arg in args:
        argbase = getattr(arg, 'aq_base', arg)
        if type(argbase) is not t:
            return 0
    return 1
safebin['same_type'] = same_type

_marker = []  # Create a new marker object.

def aq_validate(*args):
    return apply(getSecurityManager().validate, args[:4])

def __careful_getattr__(inst, name, default=_marker):
    if name[:1]!='_':
        try:
            # Try to get the attribute normally so that we don't
            # accidentally acquire when we shouldn't.
            v = getattr(inst, name)
            # Filter out the objects we can't access.
            if hasattr(inst, 'aq_acquire'):
                return inst.aq_acquire(name, aq_validate)
        except AttributeError:
            if default is not _marker:
                return default
            raise
        if getSecurityManager().validate(inst,inst,name,v):
            return v
    raise ValidationError, name
safebin['getattr'] = __careful_getattr__

def __careful_setattr__(object, name, value):
    setattr(WriteGuard(object), name, value)
safebin['setattr'] = __careful_setattr__

def __careful_delattr__(object, name):
    delattr(WriteGuard(object), name)
safebin['delattr'] = __careful_delattr__

def __careful_filter__(f, seq, skip_unauthorized=0):
    if type(seq) is type(''):
        return filter(f, seq)
    v = getSecurityManager().validate
    result = []
    a = result.append
    for el in seq:
        if v(seq, seq, None, el):
            if f(el): a(el)
        elif not skip_unauthorized:
            raise ValidationError, 'unauthorized access to element'
    return result
safebin['filter'] = __careful_filter__

def __careful_list__(seq):
    if type(seq) is type(''):
        raise TypeError, 'cannot convert string to list'
    return list(seq)
safebin['list'] = __careful_list__

def __careful_tuple__(seq):
    if type(seq) is type(''):
        raise TypeError, 'cannot convert string to tuple'
    return tuple(seq)
safebin['tuple'] = __careful_tuple__

def __careful_map__(f, *seqs):
    for seq in seqs:
        if type(seq) is type(''):
            raise TypeError, 'cannot map a string'
    return apply(map, tuple([f] + map(ReadGuard, seqs)))
safebin['map'] = __careful_map__

import sys
from string import split
def __careful_import__(mname, globals={}, locals={}, fromlist=None):
    mnameparts = split(mname, '.')
    firstmname = mnameparts[0]
    validate = getSecurityManager().validate
    module = load_module(None, None, mnameparts, validate, globals, locals)
    if module is not None:
        mtype = type(module)
        if fromlist is None:
            fromlist = ()
        try:
            for name in fromlist:
                if name == '*':
                    raise ImportError, ('"from %s import *" is not allowed'
                                        % mname)
                v = getattr(module, name, None)
                if v is None:
                    v = load_module(module, mname, [name], validate,
                                    globals, locals)
                if not validate(module, module, name, v):
                    raise "Unauthorized"
            else:
                return __import__(mname, globals, locals, fromlist)
        except "Unauthorized":
            raise ImportError, ('import of "%s" from "%s" is unauthorized'
                                % (name, mname))
    raise ImportError, 'import of "%s" is unauthorized' % mname
safebin['__import__'] = __careful_import__

def load_module(module, mname, mnameparts, validate, globals, locals):
    modules = sys.modules
    while mnameparts:
        nextname = mnameparts.pop(0)
        if mname is None:
            mname = nextname
        else:
            mname = '%s.%s' % (mname, nextname)
        nextmodule = modules.get(mname, None)
        if nextmodule is None:
            nextmodule = secureModule(mname, globals, locals)
            if nextmodule is None:
                return
        else:
            secureModule(mname)
        if module and not validate(module, module, nextname, nextmodule):
            return
        module = nextmodule
    return module

class Guard:
    mul = careful_mul
    pow = careful_pow

theGuard = Guard()

class GuardedBlock(SafeBlock):
    Mungers = SafeBlock.Mungers + [GuardedBinaryOps(theGuard),
              RedirectWrites(), RedirectReads(), LoopLimits]

class _ReadGuardWrapper:
    #def validate(self, *args):
    #    return apply(getSecurityManager().validate, args[:4])

    def __getattr__(self, name):
        ob = self.__dict__['_ob']
        return __careful_getattr__(ob, name)
        
    def __getitem__(self, i):
        ob = self.__dict__['_ob']
        v = ob[i]

        if type(ob) is type(''): return v

        if getSecurityManager().validate(ob, ob, None, v):
            return v
        raise ValidationError, 'unauthorized access to element %s' % `i`

ReadGuard = bind(ReadGuard, Wrapper=_ReadGuardWrapper)

