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
"""TALES

An implementation of a generic TALES engine
"""

__version__='$Revision: 1.6 $'[11:-2]

import re, sys, ZTUtils
from MultiMapping import MultiMapping

NAME_RE = r"[a-zA-Z][a-zA-Z0-9_]*"
_parse_expr = re.compile(r"(%s):(.*)" % NAME_RE).match
_valid_name = re.compile('%s$' % NAME_RE).match

class TALESError(Exception):
    __allow_access_to_unprotected_subobjects__ = 1
    def __init__(self, expression, info=(None, None, None)):
        self.type, self.value, self.traceback = info
        self.expression = expression
    def __str__(self):
        if self.type is not None:
            return '%s on %s in "%s"' % (self.type, self.value,
                                         self.expression)
        return self.expression

class Undefined(TALESError):
    '''Exception raised on traversal of an undefined path'''

class RegistrationError(Exception):
    '''TALES Type Registration Error'''

class CompilerError(Exception):
    '''TALES Compiler Error'''

class Iterator(ZTUtils.Iterator):
    def __init__(self, name, seq, context):
        ZTUtils.Iterator.__init__(self, seq)
        self.name = name
        self._context = context

    def next(self):
        if ZTUtils.Iterator.next(self):
            self._context.setLocal(self.name, self.seq[self.index])
            return 1
        return 0


class Engine:
    '''Expression Engine

    An instance of this class keeps a mutable collection of expression
    type handlers.  It can compile expression strings by delegating to
    these handlers.  It can provide an expression Context, which is
    capable of holding state and evaluating compiled expressions.
    '''
    Iterator = Iterator

    def __init__(self, Iterator=None):
        self.types = {}
        if Iterator is not None:
            self.Iterator = Iterator

    def registerType(self, name, handler):
        if not _valid_name(name):
            raise RegistrationError, 'Invalid Expression type "%s".' % name
        types = self.types
        if types.has_key(name):
            raise RegistrationError, (
                'Multiple registrations for Expression type "%s".' %
                name)
        types[name] = handler

    def getTypes(self):
        return self.types

    def compile(self, expression):
        m = _parse_expr(expression)
        if m:
            type, expr = m.group(1, 2)
        else:
            type = "standard"
            expr = expression
        try:
            handler = self.types[type]
        except KeyError:
            raise CompilerError, (
                'Unrecognized expression type "%s".' % type)
        try:
            return handler(type, expr, self)
        except TypeError:
            return handler(type, expr)
    
    def getContext(self, contexts=None, **kwcontexts):
        if contexts is not None:
            if kwcontexts:
                kwcontexts.update(contexts)
            else:
                kwcontexts = contexts
        return Context(self, kwcontexts)


class Context:
    '''Expression Context

    An instance of this class holds context information that it can
    use to evaluate compiled expressions.
    '''

    def __init__(self, engine, contexts):
        self._engine = engine
        self.contexts = contexts

        # Keep track of what contexts get pushed as each scope begins.
        self._ctxts_pushed = []
        # These contexts will need to be pushed.
        self._current_ctxts = {'local': 1, 'repeat': 1}
        
        contexts['local'] = lv = MultiMapping()
        init_local = contexts.get('local', None)
        if init_local:
            lv.push(init_local)
        contexts['global'] = gv = contexts.copy()
        gv['standard'] = contexts
        contexts['var'] = MultiMapping(gv, lv)
        contexts['repeat'] = rep =  MultiMapping()
        contexts['loop'] = rep # alias
        
    def beginScope(self):
        oldctxts = self._current_ctxts
        self._ctxts_pushed.append(oldctxts)
        self._current_ctxts = ctxts = {}
        for ctxname in oldctxts.keys():
            # Push fresh namespace on each local stack.
            ctxts[ctxname] = ctx = {}
            self.contexts[ctxname].push(ctx)

    def endScope(self):
        self._current_ctxts = ctxts = self._ctxts_pushed.pop()
        # Pop the ones that were pushed at the beginning of the scope.
        for ctxname in ctxts.keys():
            ctx = self.contexts[ctxname].pop()
            # Make sure there's no circular garbage
            ctx.clear()

    def setLocal(self, name, value):
        if value is not Undefined:
            self._current_ctxts['local'][name] = value

    def setGlobal(self, name, value):
        if value is not Undefined:
            self.contexts['global'][name] = value

    def setRepeat(self, name, expr):
        expr = self.evaluate(expr)
        if expr is Undefined:
            # Not sure of this
            it = self._engine.Iterator(name, [Undefined], self)
        else:
            it = self._engine.Iterator(name, expr, self)
        self._current_ctxts['repeat'][name] = it
        return it

    def evaluate(self, expression):
        if type(expression) is type(''):
            expression = self._engine.compile(expression)
        try:
            return expression(self)
        except TALESError:
            raise
        except:
            raise TALESError, (`expression`, sys.exc_info()), sys.exc_info()[2]

    evaluateValue = evaluate

    def evaluateBoolean(self, expr):
        return not not self.evaluate(expr)

    def evaluateText(self, expr):
        text = self.evaluate(expr)
        if text is not None:
            text = str(text)
        return text

    def evaluateStructure(self, expr):
        return self.evaluate(expr)

    def evaluateMacro(self, expr):
        # XXX Should return None or a macro definition
        return self.evaluate(expr)

    def getTALESError(self):
        return TALESError

    def getCancelAction(self):
        return Undefined

class SimpleExpr:
    '''Simple example of an expression type handler'''
    def __init__(self, name, expr):
        self._name = name
        self._expr = expr
    def __call__(self, econtext):
        return self._name, self._expr
    def __repr__(self):
        return '<SimpleExpr %s %s>' % (self._name, `self._expr`)






