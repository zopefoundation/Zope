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

class TALGenerator:

    inMacroUse = 0
    inMacroDef = 0
    
    def __init__(self, expressionCompiler=None, xml=1):
        if not expressionCompiler:
            from DummyEngine import DummyEngine
            expressionCompiler = DummyEngine()
        self.expressionCompiler = expressionCompiler
        self.CompilerError = expressionCompiler.getCompilerError()
        self.program = []
        self.stack = []
        self.todoStack = []
        self.macros = {}
        self.slots = {}
        self.slotStack = []
        self.xml = xml
        self.emit("version", TAL_VERSION)
        self.emit("mode", xml and "xml" or "html")

    def getCode(self):
        assert not self.stack
        assert not self.todoStack
        return self.optimize(self.program), self.macros

    def optimize(self, program):
        output = []
        collect = []
        rawseen = cursor = 0
        if self.xml:
            endsep = "/>"
        else:
            endsep = " />"
        for cursor in xrange(len(program)+1):
            try:
                item = program[cursor]
            except IndexError:
                item = (None, None)
            opcode = item[0]
            if opcode == "rawtext":
                collect.append(item[1])
                continue
            if opcode == "endTag":
                collect.append("</%s>" % item[1])
                continue
            if opcode == "startTag":
                if self.optimizeStartTag(collect, item[1], item[2], ">"):
                    continue
            if opcode == "startEndTag":
                if self.optimizeStartTag(collect, item[1], item[2], endsep):
                    continue
            if opcode in ("beginScope", "endScope"):
                # Push *Scope instructions in front of any text instructions;
                # this allows text instructions separated only by *Scope
                # instructions to be joined together.
                output.append(self.optimizeArgsList(item))
                continue
            text = string.join(collect, "")
            if text:
                i = string.rfind(text, "\n")
                if i >= 0:
                    i = len(text) - (i + 1)
                    output.append(("rawtextColumn", (text, i)))
                else:
                    output.append(("rawtextOffset", (text, len(text))))
            if opcode != None:
                output.append(self.optimizeArgsList(item))
            rawseen = cursor+1
            collect = []
        return self.optimizeCommonTriple(output)

    def optimizeArgsList(self, item):
        if len(item) == 2:
            return item
        else:
            return item[0], tuple(item[1:])

    actionIndex = {"replace":0, "insert":1, "metal":2, "tal":3, "xmlns":4,
                   0: 0, 1: 1, 2: 2, 3: 3, 4: 4}
    def optimizeStartTag(self, collect, name, attrlist, end):
        if not attrlist:
            collect.append("<%s%s" % (name, end))
            return 1
        opt = 1
        new = ["<" + name]
        for i in range(len(attrlist)):
            item = attrlist[i]
            if len(item) > 2:
                opt = 0
                name, value, action = item[:3]
                action = self.actionIndex[action]
                attrlist[i] = (name, value, action) + item[3:]
            else:
                if item[1] is None:
                    s = item[0]
                else:
                    s = "%s=%s" % (item[0], quote(item[1]))
                attrlist[i] = item[0], s
            if item[1] is None:
                new.append(" " + item[0])
            else:
                new.append(" %s=%s" % (item[0], quote(item[1])))
        if opt:
            new.append(end)
            collect.extend(new)
        return opt

    def optimizeCommonTriple(self, program):
        if len(program) < 3:
            return program
        output = program[:2]
        prev2, prev1 = output
        for item in program[2:]:
            if (  item[0] == "beginScope"
                  and prev1[0] == "setPosition"
                  and prev2[0] == "rawtextColumn"):
                position = output.pop()[1]
                text, column = output.pop()[1]
                prev1 = None, None
                closeprev = 0
                if output and output[-1][0] == "endScope":
                    closeprev = 1
                    output.pop()
                item = ("rawtextBeginScope",
                        (text, column, position, closeprev, item[1]))
            output.append(item)
            prev2 = prev1
            prev1 = item
        return output

    def todoPush(self, todo):
        self.todoStack.append(todo)

    def todoPop(self):
        return self.todoStack.pop()

    def compileExpression(self, expr):
        try:
            return self.expressionCompiler.compile(expr)
        except self.CompilerError, err:
            raise TALError('%s in expression %s' % (err.args[0], `expr`),
                           self.position)

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

    def emitStartTag(self, name, attrlist, isend=0):
        if isend:
            opcode = "startEndTag"
        else:
            opcode = "startTag"
        self.emit(opcode, name, attrlist)

    def emitEndTag(self, name):
        if self.xml and self.program and self.program[-1][0] == "startTag":
            # Minimize empty element
            self.program[-1] = ("startEndTag",) + self.program[-1][1:]
        else:
            self.emit("endTag", name)

    def emitOptTag(self, name, optTag, isend):
        program = self.popProgram() #block
        start = self.popProgram() #start tag
        if (isend or not program) and self.xml:
            # Minimize empty element
            start[-1] = ("startEndTag",) + start[-1][1:]
            isend = 1
        cexpr = optTag[0]
        if cexpr:
            cexpr = self.compileExpression(optTag[0])
        self.emit("optTag", name, cexpr, optTag[1], isend, start, program)
        
    def emitRawText(self, text):
        self.emit("rawtext", text)

    def emitText(self, text):
        self.emitRawText(cgi.escape(text))

    def emitDefines(self, defines):
        for part in splitParts(defines):
            m = re.match(
                r"(?s)\s*(?:(global|local)\s+)?(%s)\s+(.*)\Z" % NAME_RE, part)
            if not m:
                raise TALError("invalid define syntax: " + `part`,
                               self.position)
            scope, name, expr = m.group(1, 2, 3)
            scope = scope or "local"
            cexpr = self.compileExpression(expr)
            if scope == "local":
                self.emit("setLocal", name, cexpr)
            else:
                self.emit("setGlobal", name, cexpr)

    def emitOnError(self, name, onError):
        block = self.popProgram()
        key, expr = parseSubstitution(onError)
        cexpr = self.compileExpression(expr)
        if key == "text":
            self.emit("insertText", cexpr, [])
        else:
            assert key == "structure"
            self.emit("insertStructure", cexpr, {}, [])
        self.emitEndTag(name)
        handler = self.popProgram()
        self.emit("onError", block, handler)

    def emitCondition(self, expr):
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        self.emit("condition", cexpr, program)

    def emitRepeat(self, arg):
        m = re.match("(?s)\s*(%s)\s+(.*)\Z" % NAME_RE, arg)
        if not m:
            raise TALError("invalid repeat syntax: " + `arg`,
                           self.position)
        name, expr = m.group(1, 2)
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        self.emit("loop", name, cexpr, program)

    def emitSubstitution(self, arg, attrDict={}):
        key, expr = parseSubstitution(arg)
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        if key == "text":
            self.emit("insertText", cexpr, program)
        else:
            assert key == "structure"
            self.emit("insertStructure", cexpr, attrDict, program)

    def emitDefineMacro(self, macroName):
        program = self.popProgram()
        macroName = string.strip(macroName)
        if self.macros.has_key(macroName):
            raise METALError("duplicate macro definition: %s" % `macroName`,
                             self.position)
        if not re.match('%s$' % NAME_RE, macroName):
            raise METALError("invalid macro name: %s" % `macroName`,
                             self.position)
        self.macros[macroName] = program
        self.inMacroDef = self.inMacroDef - 1
        self.emit("defineMacro", macroName, program)

    def emitUseMacro(self, expr):
        cexpr = self.compileExpression(expr)
        program = self.popProgram()
        self.inMacroUse = 0
        self.emit("useMacro", expr, cexpr, self.popSlots(), program)

    def emitDefineSlot(self, slotName):
        program = self.popProgram()
        slotName = string.strip(slotName)
        if not re.match('%s$' % NAME_RE, slotName):
            raise METALError("invalid slot name: %s" % `slotName`,
                             self.position)
        self.emit("defineSlot", slotName, program)

    def emitFillSlot(self, slotName):
        program = self.popProgram()
        slotName = string.strip(slotName)
        if self.slots.has_key(slotName):
            raise METALError("duplicate fill-slot name: %s" % `slotName`,
                             self.position)
        if not re.match('%s$' % NAME_RE, slotName):
            raise METALError("invalid slot name: %s" % `slotName`,
                             self.position)
        self.slots[slotName] = program
        self.inMacroUse = 1
        self.emit("fillSlot", slotName, program)

    def unEmitWhitespace(self):
        collect = []
        i = len(self.program) - 1
        while i >= 0:
            item = self.program[i]
            if item[0] != "rawtext":
                break
            text = item[1]
            if not re.match(r"\A\s*\Z", text):
                break
            collect.append(text)
            i = i-1
        del self.program[i+1:]
        if i >= 0 and self.program[i][0] == "rawtext":
            text = self.program[i][1]
            m = re.search(r"\s+\Z", text)
            if m:
                self.program[i] = ("rawtext", text[:m.start()])
                collect.append(m.group())
        collect.reverse()
        return string.join(collect, "")

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
                self.emit("rawtext", text)
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
            item = (key, None, "insert", value)
            newlist.append(item)
        return newlist

    def emitStartElement(self, name, attrlist, taldict, metaldict,
                         position=(None, None), isend=0):
        if not taldict and not metaldict:
            # Handle the simple, common case
            self.emitStartTag(name, attrlist, isend)
            self.todoPush({})
            if isend:
                self.emitEndElement(name, isend)
            return

        self.position = position
        for key, value in taldict.items():
            if key not in KNOWN_TAL_ATTRIBUTES:
                raise TALError("bad TAL attribute: " + `key`, position)
            if not (value or key == 'omit-tag'):
                raise TALError("missing value for TAL attribute: " +
                               `key`, position)
        for key, value in metaldict.items():
            if key not in KNOWN_METAL_ATTRIBUTES:
                raise METALError("bad METAL attribute: " + `key`,
                position)
            if not value:
                raise TALError("missing value for METAL attribute: " +
                               `key`, position)
        todo = {}
        defineMacro = metaldict.get("define-macro")
        useMacro = metaldict.get("use-macro")
        defineSlot = metaldict.get("define-slot")
        fillSlot = metaldict.get("fill-slot")
        define = taldict.get("define")
        condition = taldict.get("condition")
        repeat = taldict.get("repeat")
        content = taldict.get("content")
        replace = taldict.get("replace")
        attrsubst = taldict.get("attributes")
        onError = taldict.get("on-error")
        omitTag = taldict.get("omit-tag")
        TALtag = taldict.get("tal tag")
        if len(metaldict) > 1 and (defineMacro or useMacro):
            raise METALError("define-macro and use-macro cannot be used "
                             "together or with define-slot or fill-slot",
                             position)
        if content and replace:
            raise TALError("content and replace are mutually exclusive",
                           position)

        repeatWhitespace = None
        if repeat:
            # Hack to include preceding whitespace in the loop program
            repeatWhitespace = self.unEmitNewlineWhitespace()
        if position != (None, None):
            # XXX at some point we should insist on a non-trivial position
            self.emit("setPosition", position)
        if self.inMacroUse:
            if fillSlot:
                self.pushProgram()
                todo["fillSlot"] = fillSlot
                self.inMacroUse = 0
        else:
            if fillSlot:
                raise METALError, ("fill-slot must be within a use-macro",
                                   position)
        if not self.inMacroUse:
            if defineMacro:
                self.pushProgram()
                self.emit("version", TAL_VERSION)
                self.emit("mode", self.xml and "xml" or "html")
                todo["defineMacro"] = defineMacro
                self.inMacroDef = self.inMacroDef + 1
            if useMacro:
                self.pushSlots()
                self.pushProgram()
                todo["useMacro"] = useMacro
                self.inMacroUse = 1
            if defineSlot:
                if not self.inMacroDef:
                    raise METALError, (
                        "define-slot must be within a define-macro",
                        position)
                self.pushProgram()
                todo["defineSlot"] = defineSlot

        if taldict:
            dict = {}
            for item in attrlist:
                key, value = item[:2]
                dict[key] = value
            self.emit("beginScope", dict)
            todo["scope"] = 1
        if onError:
            self.pushProgram() # handler
            self.emitStartTag(name, list(attrlist)) # Must copy attrlist!
            self.pushProgram() # block
            todo["onError"] = onError
        if define:
            self.emitDefines(define)
            todo["define"] = define
        if condition:
            self.pushProgram()
            todo["condition"] = condition
        if repeat:
            todo["repeat"] = repeat
            self.pushProgram()
            if repeatWhitespace:
                self.emitText(repeatWhitespace)
        if content:
            todo["content"] = content
        if replace:
            todo["replace"] = replace
            self.pushProgram()
        optTag = omitTag is not None or TALtag
        if optTag:
            todo["optional tag"] = omitTag, TALtag
            self.pushProgram()
        if attrsubst:
            repldict = parseAttributeReplacements(attrsubst)
            for key, value in repldict.items():
                repldict[key] = self.compileExpression(value)
        else:
            repldict = {}
        if replace:
            todo["repldict"] = repldict
            repldict = {}
        self.emitStartTag(name, self.replaceAttrs(attrlist, repldict), isend)
        if optTag:
            self.pushProgram()
        if content:
            self.pushProgram()
        if todo and position != (None, None):
            todo["position"] = position
        self.todoPush(todo)
        if isend:
            self.emitEndElement(name, isend)

    def emitEndElement(self, name, isend=0, implied=0):
        todo = self.todoPop()
        if not todo:
            # Shortcut
            if not isend:
                self.emitEndTag(name)
            return

        self.position = position = todo.get("position", (None, None))
        defineMacro = todo.get("defineMacro")
        useMacro = todo.get("useMacro")
        defineSlot = todo.get("defineSlot")
        fillSlot = todo.get("fillSlot")
        repeat = todo.get("repeat")
        content = todo.get("content")
        replace = todo.get("replace")
        condition = todo.get("condition")
        onError = todo.get("onError")
        define = todo.get("define")
        repldict = todo.get("repldict", {})
        scope = todo.get("scope")
        optTag = todo.get("optional tag")

        if implied > 0:
            if defineMacro or useMacro or defineSlot or fillSlot:
                exc = METALError
                what = "METAL"
            else:
                exc = TALError
                what = "TAL"
            raise exc("%s attributes on <%s> require explicit </%s>" %
                      (what, name, name), position)

        if content:
            self.emitSubstitution(content, {})
        if optTag:
            self.emitOptTag(name, optTag, isend)
        elif not isend:
            self.emitEndTag(name)
        if replace:
            self.emitSubstitution(replace, repldict)
        if repeat:
            self.emitRepeat(repeat)
        if condition:
            self.emitCondition(condition)
        if onError:
            self.emitOnError(name, onError)
        if scope:
            self.emit("endScope")
        if defineSlot:
            self.emitDefineSlot(defineSlot)
        if fillSlot:
            self.emitFillSlot(fillSlot)
        if useMacro:
            self.emitUseMacro(useMacro)
        if defineMacro:
            self.emitDefineMacro(defineMacro)

def test():
    t = TALGenerator()
    t.pushProgram()
    t.emit("bar")
    p = t.popProgram()
    t.emit("foo", p)

if __name__ == "__main__":
    test()
