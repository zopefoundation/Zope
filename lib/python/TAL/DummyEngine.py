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
"""
Dummy TALES engine so that I can test out the TAL implementation.
"""

import re
import sys
from string import rfind, strip

import driver

from TALDefs import NAME_RE, TALError, TALESError

Default = []

name_match = re.compile(r"(?s)(%s):(.*)\Z" % NAME_RE).match

class CompilerError(Exception):
    pass

class DummyEngine:

    position = None

    def __init__(self, macros=None):
        if macros is None:
            macros = {}
        self.macros = macros
        dict = {'nothing': None, 'default': Default}
        self.locals = self.globals = dict
        self.stack = [dict]

    def getCompilerError(self):
        return CompilerError

    def setPosition(self, position):
        self.position = position

    def compile(self, expr):
        return "$%s$" % expr

    def uncompile(self, expression):
        assert expression[:1] == "$" == expression[-1:], expression
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
        assert expression[:1] == "$" == expression[-1:], expression
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
            expr = strip(expr)
            if self.locals.has_key(expr):
                return self.locals[expr]
            elif self.globals.has_key(expr):
                return self.globals[expr]
            else:
                raise TALESError("unknown variable: %s" % `expr`)
        if type == "not":
            return not self.evaluate(expr)
        if type == "exists":
            return self.locals.has_key(expr) or self.globals.has_key(expr)
        if type == "python":
            try:
                return eval(expr, self.globals, self.locals)
            except:
                raise TALESError("evaluation error in %s" % `expr`,
                                 info=sys.exc_info())
        raise TALESError("unrecognized expression: " + `expression`)

    def evaluateValue(self, expr):
        return self.evaluate(expr)

    def evaluateBoolean(self, expr):
        return self.evaluate(expr)

    def evaluateText(self, expr):
        text = self.evaluate(expr)
        if text is not None and text is not Default:
            text = str(text)
        return text

    def evaluateStructure(self, expr):
        # XXX Should return None or a DOM tree
        return self.evaluate(expr)

    def evaluateSequence(self, expr):
        # XXX Should return a sequence
        return self.evaluate(expr)

    def evaluateMacro(self, macroName):
        assert macroName[:1] == "$" == macroName[-1:], macroName
        macroName = macroName[1:-1]
        file, localName = self.findMacroFile(macroName)
        if not file:
            # Local macro
            macro = self.macros[localName]
        else:
            # External macro
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
        doc = driver.parsefile(file)
        return doc, localName

    def findMacroFile(self, macroName):
        if not macroName:
            raise TALESError("empty macro name")
        i = rfind(macroName, '/')
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

    def getTALESError(self):
        return TALESError

    def getDefault(self):
        return Default

class Iterator:

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
