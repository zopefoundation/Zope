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
"""
Code generator for TALInterpreter intermediate code.
"""

import string
import re
import cgi

from TALDefs import *

class DummyCompiler:

    def compile(self, expr):
        return expr

class TALGenerator:

    def __init__(self, expressionCompiler=None):
        if not expressionCompiler:
            expressionCompiler = DummyCompiler()
        self.expressionCompiler = expressionCompiler
        self.program = []
        self.stack = []
        self.todoStack = []
        self.macros = {}
        self.slots = {}
        self.slotStack = []

    def getCode(self):
        return self.optimize(self.program), self.macros

    def optimize(self, program):
        output = []
        collect = []
        rawseen = cursor = 0
        for cursor in xrange(len(program)+1):
            try:
                item = program[cursor]
            except IndexError:
                item = (None, None)
            if item[0] == "rawtext":
                collect.append(item[1])
                continue
            if item[0] == "endTag":
                collect.append("</%s>" % item[1])
                continue
            if item[0] == "startTag":
                if self.optimizeStartTag(collect, item[1], item[2], ">"):
                    continue
            if item[0] == "startEndTag":
                if self.optimizeStartTag(collect, item[1], item[2], "/>"):
                    continue
            text = string.join(collect, "")
            if text:
                output.append(("rawtext", text))
            if item[0] != None:
                output.append(item)
            rawseen = cursor+1
            collect = []
        return output

    def optimizeStartTag(self, collect, name, attrlist, end):
        if not attrlist:
            collect.append("<%s%s" % (name, end))
            return 1

    def todoPush(self, todo):
        self.todoStack.append(todo)

    def todoPop(self):
        return self.todoStack.pop()

    def compileExpression(self, expr):
        return self.expressionCompiler.compile(expr)

    def pushProgram(self):
        self.stack.append(self.program)
        self.program = []

    def popProgram(self):
        program = self.program
        self.program = self.stack.pop()
        return self.optimize(program)

    def pushSlots(self):
        self.slotStack.append(self.slots)
        self.slots = {}

    def popSlots(self):
        slots = self.slots
        self.slots = self.slotStack.pop()
        return slots

    def emit(self, *instruction):
        self.program.append(instruction)

    def emitStartTag(self, name, attrlist):
        self.program.append(("startTag", name, attrlist))

    def emitEndTag(self, name):
        if self.program and self.program[-1][0] == "startTag":
            # Minimize empty element
            self.program[-1] = ("startEndTag",) + self.program[-1][1:]
        else:
            self.program.append(("endTag", name))

    def emitRawText(self, text):
        self.program.append(("rawtext", text))

    def emitText(self, text):
        self.emitRawText(cgi.escape(text))

    def emitDefines(self, defines):
        for part in splitParts(defines):
            m = re.match(
                r"\s*(?:(global|local)\s+)?(%s)\s+(.*)" % NAME_RE, part)
            if not m:
                raise TALError("invalid define syntax: " + `part`)
            scope, name, expr = m.group(1, 2, 3)
            scope = scope or "local"
            cexpr = self.compileExpression(expr)
            if scope == "local":
                self.emit("setLocal", name, cexpr)
            else:
                self.emit("setGlobal", name, cexpr)

    def emitCondition(self, expr):
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        self.emit("condition", cexpr, program)

    def emitRepeat(self, arg):
        m = re.match("\s*(%s)\s+(.*)" % NAME_RE, arg)
        if not m:
            raise TALError("invalid repeat syntax: " + `repeat`)
        name, expr = m.group(1, 2)
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        self.emit("loop", name, cexpr, program)

    def emitSubstitution(self, arg, attrDict={}):
        key, expr = parseSubstitution(arg)
        if not key:
            raise TALError("Bad syntax in insert/replace: " + `arg`)
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        if key == "text":
            self.emit("insertText", cexpr, program)
        else:
            assert key == "structure"
            self.emit("insertStructure", cexpr, attrDict, program)

    def emitDefineMacro(self, macroName):
        program = self.popProgram()
        if self.macros.has_key(macroName):
            raise METALError("duplicate macro definition: %s" % macroName)
        self.macros[macroName] = program
        self.emit("defineMacro", macroName, program)

    def emitUseMacro(self, expr):
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        self.emit("useMacro", cexpr, self.popSlots(), program)

    def emitDefineSlot(self, slotName):
        program = self.popProgram()
        self.emit("defineSlot", slotName, program)

    def emitFillSlot(self, slotName):
        program = self.popProgram()
        if self.slots.has_key(slotName):
            raise METALError("duplicate slot definition: %s" % slotName)
        self.slots[slotName] = program
        self.emit("fillSlot", slotName, program)

    def unEmitNewlineWhitespace(self):
        collect = []
        i = len(self.program)
        while i > 0:
            i = i-1
            item = self.program[i]
            if item[0] != "rawtext":
                break
            text = item[1]
            if re.match(r"\A[ \t]*\Z", text):
                collect.append(text)
                continue
            m = re.match(r"(?s)^(.*)(\n[ \t]*)\Z", text)
            if not m:
                break
            text, rest = m.group(1, 2)
            collect.reverse()
            rest = rest + string.join(collect, "")
            del self.program[i:]
            if text:
                self.program.append(("rawtext", text))
            return rest
        return None

    def replaceAttrs(self, attrlist, repldict):
        if not repldict:
            return attrlist
        newlist = []
        for item in attrlist:
            key = item[0]
            if repldict.has_key(key):
                item = item[:2] + ("replace", repldict[key])
                del repldict[key]
            newlist.append(item)
        for key, value in repldict.items(): # Add dynamic-only attributes
            item = (key, "", "replace", value)
            newlist.append(item)
        return newlist

    def emitStartElement(self, name, attrlist, taldict, metaldict):
        for key in taldict.keys():
            if key not in KNOWN_TAL_ATTRIBUTES:
                raise TALError("bad TAL attribute: " + `key`)
        for key in metaldict.keys():
            if key not in KNOWN_METAL_ATTRIBUTES:
                raise METALError("bad METAL attribute: " + `key`)
        todo = {}
        defineMacro = metaldict.get("define-macro")
        useMacro = metaldict.get("use-macro")
        defineSlot = metaldict.get("define-slot")
        fillSlot = metaldict.get("fill-slot")
        defines = taldict.get("define")
        condition = taldict.get("condition")
        content = taldict.get("content")
        replace = taldict.get("replace")
        repeat = taldict.get("repeat")
        attrsubst = taldict.get("attributes")
        n = 0
        if defineMacro: n = n+1
        if useMacro: n = n+1
        if fillSlot: n = n+1
        if defineSlot: n = n+1
        if n > 1:
            raise METALError("only one METAL attribute per element")
        n = 0
        if content: n = n+1
        if replace: n + n+1
        if repeat: n = n+1
        if n > 1:
            raise TALError("can't use content, replace, repeat together")
        repeatWhitespace = None
        if repeat:
            # Hack to include preceding whitespace in the loop program
            repeatWhitespace = self.unEmitNewlineWhitespace()
        if defineMacro:
            self.pushProgram()
            todo["defineMacro"] = defineMacro
        if useMacro:
            self.pushSlots()
            self.pushProgram()
            todo["useMacro"] = useMacro
        if defineSlot:
            self.pushProgram()
            todo["defineSlot"] = defineSlot
        if fillSlot:
            self.pushProgram()
            todo["fillSlot"] = fillSlot
        if defines:
            self.emit("beginScope")
            self.emitDefines(defines)
            todo["define"] = defines
        if condition:
            self.pushProgram()
            todo["condition"] = condition
        if content:
            todo["content"] = content
        elif replace:
            todo["replace"] = replace
            self.pushProgram()
        elif repeat:
            todo["repeat"] = repeat
            self.emit("beginScope")
            self.pushProgram()
            if repeatWhitespace:
                self.emitText(repeatWhitespace)
        if attrsubst:
            repldict = parseAttributeReplacements(attrsubst)
        else:
            repldict = {}
        self.emitStartTag(name, self.replaceAttrs(attrlist, repldict))
        if content:
            self.pushProgram()
        self.todoPush(todo)

    def emitEndElement(self, name):
        todo = self.todoPop()
        if not todo:
            # Shortcut
            self.emitEndTag(name)
            return
        content = todo.get("content")
        if content:
            self.emitSubstitution(content)
        self.emitEndTag(name)
        repeat = todo.get("repeat")
        if repeat:
            self.emitRepeat(repeat)
            self.emit("endScope")
        replace = todo.get("replace")
        if replace:
            self.emitSubstitution(replace)
        condition = todo.get("condition")
        if condition:
            self.emitCondition(condition)
        if todo.get("define"):
            self.emit("endScope")
        defineMacro = todo.get("defineMacro")
        useMacro = todo.get("useMacro")
        defineSlot = todo.get("defineSlot")
        fillSlot = todo.get("fillSlot")
        if defineMacro:
            self.emitDefineMacro(defineMacro)
        if useMacro:
            self.emitUseMacro(useMacro)
        if defineSlot:
            self.emitDefineSlot(defineSlot)
        if fillSlot:
            self.emitFillSlot(fillSlot)

def test():
    t = TALGenerator()
    t.pushProgram()
    t.emit("bar")
    p = t.popProgram()
    t.emit("foo", p)

if __name__ == "__main__":
    test()
