##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
Dummy TALES engine so that I can test out the TAL implementation.
"""

import re
import sys

from TALDefs import NAME_RE, TALESError, ErrorInfo
from ITALES import ITALESCompiler, ITALESEngine
from DocumentTemplate.DT_Util import ustr

class _Default:
    pass
Default = _Default()

name_match = re.compile(r"(?s)(%s):(.*)\Z" % NAME_RE).match

class CompilerError(Exception):
    pass

class DummyEngine:

    position = None
    source_file = None

    __implements__ = ITALESCompiler, ITALESEngine

    def __init__(self, macros=None):
        if macros is None:
            macros = {}
        self.macros = macros
        dict = {'nothing': None, 'default': Default}
        self.locals = self.globals = dict
        self.stack = [dict]
        self.translationService = DummyTranslationService()

    def getCompilerError(self):
        return CompilerError

    def getCompiler(self):
        return self

    def setSourceFile(self, source_file):
        self.source_file = source_file

    def setPosition(self, position):
        self.position = position

    def compile(self, expr):
        return "$%s$" % expr

    def uncompile(self, expression):
        assert (expression.startswith("$") and expression.endswith("$"),
            expression)
        return expression[1:-1]

    def beginScope(self):
        self.stack.append(self.locals)

    def endScope(self):
        assert len(self.stack) > 1, "more endScope() than beginScope() calls"
        self.locals = self.stack.pop()

    def setLocal(self, name, value):
        if self.locals is self.stack[-1]:
            # Unmerge this scope's locals from previous scope of first set
            self.locals = self.locals.copy()
        self.locals[name] = value

    def setGlobal(self, name, value):
        self.globals[name] = value

    def evaluate(self, expression):
        assert (expression.startswith("$") and expression.endswith("$"),
            expression)
        expression = expression[1:-1]
        m = name_match(expression)
        if m:
            type, expr = m.group(1, 2)
        else:
            type = "path"
            expr = expression
        if type in ("string", "str"):
            return expr
        if type in ("path", "var", "global", "local"):
            return self.evaluatePathOrVar(expr)
        if type == "not":
            return not self.evaluate(expr)
        if type == "exists":
            return self.locals.has_key(expr) or self.globals.has_key(expr)
        if type == "python":
            try:
                return eval(expr, self.globals, self.locals)
            except:
                raise TALESError("evaluation error in %s" % `expr`)
        if type == "position":
            # Insert the current source file name, line number,
            # and column offset.
            if self.position:
                lineno, offset = self.position
            else:
                lineno, offset = None, None
            return '%s (%s,%s)' % (self.source_file, lineno, offset)
        raise TALESError("unrecognized expression: " + `expression`)

    def evaluatePathOrVar(self, expr):
        expr = expr.strip()
        if self.locals.has_key(expr):
            return self.locals[expr]
        elif self.globals.has_key(expr):
            return self.globals[expr]
        else:
            raise TALESError("unknown variable: %s" % `expr`)

    def evaluateValue(self, expr):
        return self.evaluate(expr)

    def evaluateBoolean(self, expr):
        return self.evaluate(expr)

    def evaluateText(self, expr):
        text = self.evaluate(expr)
        if text is not None and text is not Default:
            text = ustr(text)
        return text

    def evaluateStructure(self, expr):
        # XXX Should return None or a DOM tree
        return self.evaluate(expr)

    def evaluateSequence(self, expr):
        # XXX Should return a sequence
        return self.evaluate(expr)

    def evaluateMacro(self, macroName):
        assert (macroName.startswith("$") and macroName.endswith("$"),
            macroName)
        macroName = macroName[1:-1]
        file, localName = self.findMacroFile(macroName)
        if not file:
            # Local macro
            macro = self.macros[localName]
        else:
            # External macro
            import driver
            program, macros = driver.compilefile(file)
            macro = macros.get(localName)
            if not macro:
                raise TALESError("macro %s not found in file %s" %
                                 (localName, file))
        return macro

    def findMacroDocument(self, macroName):
        file, localName = self.findMacroFile(macroName)
        if not file:
            return file, localName
        import driver
        doc = driver.parsefile(file)
        return doc, localName

    def findMacroFile(self, macroName):
        if not macroName:
            raise TALESError("empty macro name")
        i = macroName.rfind('/')
        if i < 0:
            # No slash -- must be a locally defined macro
            return None, macroName
        else:
            # Up to last slash is the filename
            fileName = macroName[:i]
            localName = macroName[i+1:]
            return fileName, localName

    def setRepeat(self, name, expr):
        seq = self.evaluateSequence(expr)
        return Iterator(name, seq, self)

    def createErrorInfo(self, err, position):
        return ErrorInfo(err, position)

    def getDefault(self):
        return Default

    def translate(self, domain, msgid, mapping, default=None):
        return self.translationService.translate(domain, msgid, mapping,
                                                 default=default)


class Iterator:

    # This is not an implementation of a Python iterator.  The next()
    # method returns true or false to indicate whether another item is
    # available; if there is another item, the iterator instance calls
    # setLocal() on the evaluation engine passed to the constructor.

    def __init__(self, name, seq, engine):
        self.name = name
        self.seq = seq
        self.engine = engine
        self.nextIndex = 0

    def next(self):
        i = self.nextIndex
        try:
            item = self.seq[i]
        except IndexError:
            return 0
        self.nextIndex = i+1
        self.engine.setLocal(self.name, item)
        return 1

class DummyDomain:

    def translate(self, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        # This is a fake translation service which simply uppercases non
        # ${name} placeholder text in the message id.
        #
        # First, transform a string with ${name} placeholders into a list of
        # substrings.  Then upcase everything but the placeholders, then glue
        # things back together.

        # simulate an unknown msgid by returning None
        text = msgid
        if msgid == "don't translate me":
            if default is not None:
                text = default
        else:
            text = msgid.upper()

        def repl(m, mapping=mapping):
            return ustr(mapping[m.group(m.lastindex).lower()])
        cre = re.compile(r'\$(?:(%s)|\{(%s)\})' % (NAME_RE, NAME_RE))
        return cre.sub(repl, text)

class DummyTranslationService:

    def translate(self, domain, msgid, mapping=None, context=None,
                  target_language=None, default=None):
        return self.getDomain(domain).translate(msgid, mapping, context,
                                                target_language,
                                                default=default)

    def getDomain(self, domain):
        return DummyDomain()
