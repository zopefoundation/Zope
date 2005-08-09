##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""TALES

An implementation of a generic TALES engine
"""

__version__='$Revision: 1.39 $'[11:-2]

import re, sys, ZTUtils
from weakref import ref
from MultiMapping import MultiMapping
from DocumentTemplate.DT_Util import ustr
from GlobalTranslationService import getGlobalTranslationService
from zExceptions import Unauthorized

StringType = type('')

NAME_RE = r"[a-zA-Z][a-zA-Z0-9_]*"
_parse_expr = re.compile(r"(%s):" % NAME_RE).match
_valid_name = re.compile('%s$' % NAME_RE).match

class TALESError(Exception):
    """Error during TALES expression evaluation"""

class Undefined(TALESError):
    '''Exception raised on traversal of an undefined path'''

class RegistrationError(Exception):
    '''TALES Type Registration Error'''

class CompilerError(Exception):
    '''TALES Compiler Error'''

class Default:
    '''Retain Default'''
Default = Default()

class SafeMapping(MultiMapping):
    '''Mapping with security declarations and limited method exposure.

    Since it subclasses MultiMapping, this class can be used to wrap
    one or more mapping objects.  Restricted Python code will not be
    able to mutate the SafeMapping or the wrapped mappings, but will be
    able to read any value.
    '''
    __allow_access_to_unprotected_subobjects__ = 1
    push = pop = None

    _push = MultiMapping.push
    _pop = MultiMapping.pop


class Iterator(ZTUtils.Iterator):
    def __init__(self, name, seq, context):
        ZTUtils.Iterator.__init__(self, seq)
        self.name = name
        self._context_ref = ref(context)

    def next(self):
        if ZTUtils.Iterator.next(self):
            context = self._context_ref()
            if context is not None:
                context.setLocal(self.name, self.item)
            return 1
        return 0


class ErrorInfo:
    """Information about an exception passed to an on-error handler."""
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, err, position=(None, None)):
        if isinstance(err, Exception):
            self.type = err.__class__
            self.value = err
        else:
            self.type = err
            self.value = None
        self.lineno = position[0]
        self.offset = position[1]


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
            type = m.group(1)
            expr = expression[m.end():]
        else:
            type = "standard"
            expr = expression
        try:
            handler = self.types[type]
        except KeyError:
            raise CompilerError, (
                'Unrecognized expression type "%s".' % type)
        return handler(type, expr, self)

    def getContext(self, contexts=None, **kwcontexts):
        if contexts is not None:
            if kwcontexts:
                kwcontexts.update(contexts)
            else:
                kwcontexts = contexts
        return Context(self, kwcontexts)

    def getCompilerError(self):
        return CompilerError

class Context:
    '''Expression Context

    An instance of this class holds context information that it can
    use to evaluate compiled expressions.
    '''

    _context_class = SafeMapping
    position = (None, None)
    source_file = None

    def __init__(self, compiler, contexts):
        self._compiler = compiler
        self.contexts = contexts
        contexts['nothing'] = None
        contexts['default'] = Default

        self.repeat_vars = rv = {}
        # Wrap this, as it is visible to restricted code
        contexts['repeat'] = rep =  self._context_class(rv)
        contexts['loop'] = rep # alias

        self.global_vars = gv = contexts.copy()
        self.local_vars = lv = {}
        self.vars = self._context_class(gv, lv)

        # Keep track of what needs to be popped as each scope ends.
        self._scope_stack = []

    def getCompiler(self):
        return self._compiler

    def beginScope(self):
        self._scope_stack.append([self.local_vars.copy()])

    def endScope(self):
        scope = self._scope_stack.pop()
        self.local_vars = lv = scope[0]
        v = self.vars
        v._pop()
        v._push(lv)
        # Pop repeat variables, if any
        i = len(scope) - 1
        while i:
            name, value = scope[i]
            if value is None:
                del self.repeat_vars[name]
            else:
                self.repeat_vars[name] = value
            i = i - 1

    def setLocal(self, name, value):
        self.local_vars[name] = value

    def setGlobal(self, name, value):
        self.global_vars[name] = value

    def setRepeat(self, name, expr):
        expr = self.evaluate(expr)
        if not expr:
            return self._compiler.Iterator(name, (), self)
        it = self._compiler.Iterator(name, expr, self)
        old_value = self.repeat_vars.get(name)
        self._scope_stack[-1].append((name, old_value))
        self.repeat_vars[name] = it
        return it

    def evaluate(self, expression,
                 isinstance=isinstance, StringType=StringType):
        if isinstance(expression, StringType):
            expression = self._compiler.compile(expression)
        __traceback_supplement__ = (
            TALESTracebackSupplement, self, expression)
        return expression(self)

    evaluateValue = evaluate
    evaluateBoolean = evaluate

    def evaluateText(self, expr):
        text = self.evaluate(expr)
        if text is Default or text is None:
            return text
        return ustr(text)

    def evaluateStructure(self, expr):
        return self.evaluate(expr)
    evaluateStructure = evaluate

    def evaluateMacro(self, expr):
        # XXX Should return None or a macro definition
        return self.evaluate(expr)
    evaluateMacro = evaluate

    def createErrorInfo(self, err, position):
        return ErrorInfo(err, position)

    def getDefault(self):
        return Default

    def setSourceFile(self, source_file):
        self.source_file = source_file

    def setPosition(self, position):
        self.position = position

    def translate(self, domain, msgid, mapping=None,
                  context=None, target_language=None, default=None):
        if context is None:
            context = self.contexts.get('here')
        return getGlobalTranslationService().translate(
            domain, msgid, mapping=mapping,
            context=context,
            default=default,
            target_language=target_language)

class TALESTracebackSupplement:
    """Implementation of ITracebackSupplement"""
    def __init__(self, context, expression):
        self.context = context
        self.source_url = context.source_file
        self.line = context.position[0]
        self.column = context.position[1]
        self.expression = repr(expression)

    def getInfo(self, as_html=0):
        import pprint
        from cgi import escape
        data = self.context.contexts.copy()
        try:
            s = pprint.pformat(data)
        except Unauthorized, e:
            s = '   - %s: %s' % (getattr(e, '__class__', type(e)), e)
            if as_html:
                s = escape(s)
            return s
        if not as_html:
            return '   - Names:\n      %s' % s.replace('\n', '\n      ')
        else:
            return '<b>Names:</b><pre>%s</pre>' % (escape(s))


class SimpleExpr:
    '''Simple example of an expression type handler'''
    def __init__(self, name, expr, engine):
        self._name = name
        self._expr = expr
    def __call__(self, econtext):
        return self._name, self._expr
    def __repr__(self):
        return '<SimpleExpr %s %s>' % (self._name, `self._expr`)
