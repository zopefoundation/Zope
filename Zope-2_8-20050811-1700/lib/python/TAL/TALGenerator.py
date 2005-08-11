##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""
Code generator for TALInterpreter intermediate code.
"""

import re
import cgi

import TALDefs

from TALDefs import NAME_RE, TAL_VERSION
from TALDefs import I18NError, METALError, TALError
from TALDefs import parseSubstitution
from TranslationContext import TranslationContext, DEFAULT_DOMAIN

I18N_REPLACE = 1
I18N_CONTENT = 2
I18N_EXPRESSION = 3

_name_rx = re.compile(NAME_RE)


class TALGenerator:

    inMacroUse = 0
    inMacroDef = 0
    source_file = None

    def __init__(self, expressionCompiler=None, xml=1, source_file=None):
        if not expressionCompiler:
            from DummyEngine import DummyEngine
            expressionCompiler = DummyEngine()
        self.expressionCompiler = expressionCompiler
        self.CompilerError = expressionCompiler.getCompilerError()
        # This holds the emitted opcodes representing the input
        self.program = []
        # The program stack for when we need to do some sub-evaluation for an
        # intermediate result.  E.g. in an i18n:name tag for which the
        # contents describe the ${name} value.
        self.stack = []
        # Another stack of postponed actions.  Elements on this stack are a
        # dictionary; key/values contain useful information that
        # emitEndElement needs to finish its calculations
        self.todoStack = []
        self.macros = {}
        self.slots = {}
        self.slotStack = []
        self.xml = xml
        self.emit("version", TAL_VERSION)
        self.emit("mode", xml and "xml" or "html")
        if source_file is not None:
            self.source_file = source_file
            self.emit("setSourceFile", source_file)
        self.i18nContext = TranslationContext()
        self.i18nLevel = 0

    def getCode(self):
        assert not self.stack
        assert not self.todoStack
        return self.optimize(self.program), self.macros

    def optimize(self, program):
        output = []
        collect = []
        cursor = 0
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
            if opcode == 'noop':
                # This is a spacer for end tags in the face of i18n:name
                # attributes.  We can't let the optimizer collect immediately
                # following end tags into the same rawtextOffset.
                opcode = None
                pass
            text = "".join(collect)
            if text:
                i = text.rfind("\n")
                if i >= 0:
                    i = len(text) - (i + 1)
                    output.append(("rawtextColumn", (text, i)))
                else:
                    output.append(("rawtextOffset", (text, len(text))))
            if opcode != None:
                output.append(self.optimizeArgsList(item))
            collect = []
        return self.optimizeCommonTriple(output)

    def optimizeArgsList(self, item):
        if len(item) == 2:
            return item
        else:
            return item[0], tuple(item[1:])

    # These codes are used to indicate what sort of special actions
    # are needed for each special attribute.  (Simple attributes don't
    # get action codes.)
    #
    # The special actions (which are modal) are handled by
    # TALInterpreter.attrAction() and .attrAction_tal().
    #
    # Each attribute is represented by a tuple:
    #
    # (name, value)                 -- a simple name/value pair, with
    #                                  no special processing
    #
    # (name, value, action, *extra) -- attribute with special
    #                                  processing needs, action is a
    #                                  code that indicates which
    #                                  branch to take, and *extra
    #                                  contains additional,
    #                                  action-specific information
    #                                  needed by the processing
    #
    def optimizeStartTag(self, collect, name, attrlist, end):
        # return true if the tag can be converted to plain text
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
                attrlist[i] = (name, value, action) + item[3:]
            else:
                if item[1] is None:
                    s = item[0]
                else:
                    s = '%s="%s"' % (item[0], TALDefs.attrEscape(item[1]))
                attrlist[i] = item[0], s
                new.append(" " + s)
        # if no non-optimizable attributes were found, convert to plain text
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
            if ( item[0] == "beginScope"
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
        for part in TALDefs.splitParts(defines):
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

    def emitOnError(self, name, onError, TALtag, isend):
        block = self.popProgram()
        key, expr = parseSubstitution(onError)
        cexpr = self.compileExpression(expr)
        if key == "text":
            self.emit("insertText", cexpr, [])
        else:
            assert key == "structure"
            self.emit("insertStructure", cexpr, {}, [])
        if TALtag:
            self.emitOptTag(name, (None, 1), isend)
        else:
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

    def emitI18nVariable(self, stuff):
        # Used for i18n:name attributes.  arg is extra information describing
        # how the contents of the variable should get filled in, and it will
        # either be a 1-tuple or a 2-tuple.  If arg[0] is None, then the
        # i18n:name value is taken implicitly from the contents of the tag,
        # e.g. "I live in <span i18n:name="country">the USA</span>".  In this
        # case, arg[1] is the opcode sub-program describing the contents of
        # the tag.
        #
        # When arg[0] is not None, it contains the tal expression used to
        # calculate the contents of the variable, e.g.
        # "I live in <span i18n:name="country"
        #                  tal:replace="here/countryOfOrigin" />"
        varname, action, expression = stuff
        m = _name_rx.match(varname)
        if m is None or m.group() != varname:
            raise TALError("illegal i18n:name: %r" % varname, self.position)
        key = cexpr = None
        program = self.popProgram()
        if action == I18N_REPLACE:
            # This is a tag with an i18n:name and a tal:replace (implicit or
            # explicit).  Get rid of the first and last elements of the
            # program, which are the start and end tag opcodes of the tag.
            program = program[1:-1]
        elif action == I18N_CONTENT:
            # This is a tag with an i18n:name and a tal:content
            # (explicit-only).  Keep the first and last elements of the
            # program, so we keep the start and end tag output.
            pass
        else:
            assert action == I18N_EXPRESSION
            key, expr = parseSubstitution(expression)
            cexpr = self.compileExpression(expr)
        self.emit('i18nVariable',
                  varname, program, cexpr, int(key == "structure"))

    def emitTranslation(self, msgid, i18ndata):
        program = self.popProgram()
        if i18ndata is None:
            self.emit('insertTranslation', msgid, program)
        else:
            key, expr = parseSubstitution(i18ndata)
            cexpr = self.compileExpression(expr)
            assert key == 'text'
            self.emit('insertTranslation', msgid, program, cexpr)

    def emitDefineMacro(self, macroName):
        program = self.popProgram()
        macroName = macroName.strip()
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
        slotName = slotName.strip()
        if not re.match('%s$' % NAME_RE, slotName):
            raise METALError("invalid slot name: %s" % `slotName`,
                             self.position)
        self.emit("defineSlot", slotName, program)

    def emitFillSlot(self, slotName):
        program = self.popProgram()
        slotName = slotName.strip()
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
        return "".join(collect)

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
            rest = rest + "".join(collect)
            del self.program[i:]
            if text:
                self.emit("rawtext", text)
            return rest
        return None

    def replaceAttrs(self, attrlist, repldict):
        # Each entry in attrlist starts like (name, value).
        # Result is (name, value, action, expr, xlat) if there is a
        # tal:attributes entry for that attribute.  Additional attrs
        # defined only by tal:attributes are added here.
        #
        # (name, value, action, expr, xlat)
        if not repldict:
            return attrlist
        newlist = []
        for item in attrlist:
            key = item[0]
            if repldict.has_key(key):
                expr, xlat, msgid = repldict[key]
                item = item[:2] + ("replace", expr, xlat, msgid)
                del repldict[key]
            newlist.append(item)
        # Add dynamic-only attributes
        for key, (expr, xlat, msgid) in repldict.items():
            newlist.append((key, None, "insert", expr, xlat, msgid))
        return newlist

    def emitStartElement(self, name, attrlist, taldict, metaldict, i18ndict,
                         position=(None, None), isend=0):
        if not taldict and not metaldict and not i18ndict:
            # Handle the simple, common case
            self.emitStartTag(name, attrlist, isend)
            self.todoPush({})
            if isend:
                self.emitEndElement(name, isend)
            return

        self.position = position
        for key, value in taldict.items():
            if key not in TALDefs.KNOWN_TAL_ATTRIBUTES:
                raise TALError("bad TAL attribute: " + `key`, position)
            if not (value or key == 'omit-tag'):
                raise TALError("missing value for TAL attribute: " +
                               `key`, position)
        for key, value in metaldict.items():
            if key not in TALDefs.KNOWN_METAL_ATTRIBUTES:
                raise METALError("bad METAL attribute: " + `key`,
                                 position)
            if not value:
                raise TALError("missing value for METAL attribute: " +
                               `key`, position)
        for key, value in i18ndict.items():
            if key not in TALDefs.KNOWN_I18N_ATTRIBUTES:
                raise I18NError("bad i18n attribute: " + `key`, position)
            if not value and key in ("attributes", "data", "id"):
                raise I18NError("missing value for i18n attribute: " +
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
        i18nattrs = i18ndict.get("attributes")
        # Preserve empty string if implicit msgids are used.  We'll generate
        # code with the msgid='' and calculate the right implicit msgid during
        # interpretation phase.
        msgid = i18ndict.get("translate")
        varname = i18ndict.get('name')
        i18ndata = i18ndict.get('data')

        if varname and not self.i18nLevel:
            raise I18NError(
                "i18n:name can only occur inside a translation unit",
                position)

        if i18ndata and not msgid:
            raise I18NError("i18n:data must be accompanied by i18n:translate",
                            position)

        if len(metaldict) > 1 and (defineMacro or useMacro):
            raise METALError("define-macro and use-macro cannot be used "
                             "together or with define-slot or fill-slot",
                             position)
        if replace:
            if content:
                raise TALError(
                    "tal:content and tal:replace are mutually exclusive",
                    position)
            if msgid is not None:
                raise I18NError(
                    "i18n:translate and tal:replace are mutually exclusive",
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
                if self.source_file is not None:
                    self.emit("setSourceFile", self.source_file)
                todo["fillSlot"] = fillSlot
                self.inMacroUse = 0
        else:
            if fillSlot:
                raise METALError("fill-slot must be within a use-macro",
                                 position)
        if not self.inMacroUse:
            if defineMacro:
                self.pushProgram()
                self.emit("version", TAL_VERSION)
                self.emit("mode", self.xml and "xml" or "html")
                if self.source_file is not None:
                    self.emit("setSourceFile", self.source_file)
                todo["defineMacro"] = defineMacro
                self.inMacroDef = self.inMacroDef + 1
            if useMacro:
                self.pushSlots()
                self.pushProgram()
                todo["useMacro"] = useMacro
                self.inMacroUse = 1
            if defineSlot:
                if not self.inMacroDef:
                    raise METALError(
                        "define-slot must be within a define-macro",
                        position)
                self.pushProgram()
                todo["defineSlot"] = defineSlot

        if defineSlot or i18ndict:

            domain = i18ndict.get("domain") or self.i18nContext.domain
            source = i18ndict.get("source") or self.i18nContext.source
            target = i18ndict.get("target") or self.i18nContext.target
            if (  domain != DEFAULT_DOMAIN
                  or source is not None
                  or target is not None):
                self.i18nContext = TranslationContext(self.i18nContext,
                                                      domain=domain,
                                                      source=source,
                                                      target=target)
                self.emit("beginI18nContext",
                          {"domain": domain, "source": source,
                           "target": target})
                todo["i18ncontext"] = 1
        if taldict or i18ndict:
            dict = {}
            for item in attrlist:
                key, value = item[:2]
                dict[key] = value
            self.emit("beginScope", dict)
            todo["scope"] = 1
        if onError:
            self.pushProgram() # handler
            if TALtag:
                self.pushProgram() # start
            self.emitStartTag(name, list(attrlist)) # Must copy attrlist!
            if TALtag:
                self.pushProgram() # start
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
            if varname:
                todo['i18nvar'] = (varname, I18N_CONTENT, None)
                todo["content"] = content
                self.pushProgram()
            else:
                todo["content"] = content
        elif replace:
            # tal:replace w/ i18n:name has slightly different semantics.  What
            # we're actually replacing then is the contents of the ${name}
            # placeholder.
            if varname:
                todo['i18nvar'] = (varname, I18N_EXPRESSION, replace)
            else:
                todo["replace"] = replace
            self.pushProgram()
        # i18n:name w/o tal:replace uses the content as the interpolation
        # dictionary values
        elif varname:
            todo['i18nvar'] = (varname, I18N_REPLACE, None)
            self.pushProgram()
        if msgid is not None:
            self.i18nLevel += 1
            todo['msgid'] = msgid
        if i18ndata:
            todo['i18ndata'] = i18ndata
        optTag = omitTag is not None or TALtag
        if optTag:
            todo["optional tag"] = omitTag, TALtag
            self.pushProgram()
        if attrsubst or i18nattrs:
            if attrsubst:
                repldict = TALDefs.parseAttributeReplacements(attrsubst,
                                                              self.xml)
            else:
                repldict = {}
            if i18nattrs:
                i18nattrs = _parseI18nAttributes(i18nattrs, attrlist, repldict,
                                                 self.position, self.xml,
                                                 self.source_file)
            else:
                i18nattrs = {}
            # Convert repldict's name-->expr mapping to a
            # name-->(compiled_expr, translate) mapping
            for key, value in repldict.items():
                if i18nattrs.get(key, None):
                    raise I18NError(
                      ("attribute [%s] cannot both be part of tal:attributes" +
                      " and have a msgid in i18n:attributes") % key,
                    position)
                ce = self.compileExpression(value)
                repldict[key] = ce, key in i18nattrs, i18nattrs.get(key)
            for key in i18nattrs:
                if not repldict.has_key(key):
                    repldict[key] = None, 1, i18nattrs.get(key)
        else:
            repldict = {}
        if replace:
            todo["repldict"] = repldict
            repldict = {}
        self.emitStartTag(name, self.replaceAttrs(attrlist, repldict), isend)
        if optTag:
            self.pushProgram()
        if content and not varname:
            self.pushProgram()
        if msgid is not None:
            self.pushProgram()
        if content and varname:
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
        repldict = todo.get("repldict", {})
        scope = todo.get("scope")
        optTag = todo.get("optional tag")
        msgid = todo.get('msgid')
        i18ncontext = todo.get("i18ncontext")
        varname = todo.get('i18nvar')
        i18ndata = todo.get('i18ndata')

        if implied > 0:
            if defineMacro or useMacro or defineSlot or fillSlot:
                exc = METALError
                what = "METAL"
            else:
                exc = TALError
                what = "TAL"
            raise exc("%s attributes on <%s> require explicit </%s>" %
                      (what, name, name), position)

        # If there's no tal:content or tal:replace in the tag with the
        # i18n:name, tal:replace is the default.
        if content:
            self.emitSubstitution(content, {})
        # If we're looking at an implicit msgid, emit the insertTranslation
        # opcode now, so that the end tag doesn't become part of the implicit
        # msgid.  If we're looking at an explicit msgid, it's better to emit
        # the opcode after the i18nVariable opcode so we can better handle
        # tags with both of them in them (and in the latter case, the contents
        # would be thrown away for msgid purposes).
        #
        # Still, we should emit insertTranslation opcode before i18nVariable
        # in case tal:content, i18n:translate and i18n:name in the same tag
        if msgid is not None:
            if (not varname) or (
                varname and (varname[1] == I18N_CONTENT)):
                self.emitTranslation(msgid, i18ndata)
            self.i18nLevel -= 1
        if optTag:
            self.emitOptTag(name, optTag, isend)
        elif not isend:
            # If we're processing the end tag for a tag that contained
            # i18n:name, we need to make sure that optimize() won't collect
            # immediately following end tags into the same rawtextOffset, so
            # put a spacer here that the optimizer will recognize.
            if varname:
                self.emit('noop')
            self.emitEndTag(name)
        # If i18n:name appeared in the same tag as tal:replace then we're
        # going to do the substitution a little bit differently.  The results
        # of the expression go into the i18n substitution dictionary.
        if replace:
            self.emitSubstitution(replace, repldict)
        elif varname:
            # o varname[0] is the variable name
            # o varname[1] is either
            #   - I18N_REPLACE for implicit tal:replace
            #   - I18N_CONTENT for tal:content
            #   - I18N_EXPRESSION for explicit tal:replace
            # o varname[2] will be None for the first two actions and the
            #   replacement tal expression for the third action.  This
            #   can include a 'text' or 'structure' indicator.
            assert (varname[1]
                    in [I18N_REPLACE, I18N_CONTENT, I18N_EXPRESSION])
            self.emitI18nVariable(varname)
        # Do not test for "msgid is not None", i.e. we only want to test for
        # explicit msgids here.  See comment above.
        if msgid is not None: 
            # in case tal:content, i18n:translate and i18n:name in the
            # same tag insertTranslation opcode has already been
            # emitted
            if varname and (varname[1] <> I18N_CONTENT):
                self.emitTranslation(msgid, i18ndata)
        if repeat:
            self.emitRepeat(repeat)
        if condition:
            self.emitCondition(condition)
        if onError:
            self.emitOnError(name, onError, optTag and optTag[1], isend)
        if scope:
            self.emit("endScope")
        if i18ncontext:
            self.emit("endI18nContext")
            assert self.i18nContext.parent is not None
            self.i18nContext = self.i18nContext.parent
        if defineSlot:
            self.emitDefineSlot(defineSlot)
        if fillSlot:
            self.emitFillSlot(fillSlot)
        if useMacro:
            self.emitUseMacro(useMacro)
        if defineMacro:
            self.emitDefineMacro(defineMacro)


def _parseI18nAttributes(i18nattrs, attrlist, repldict, position,
                         xml, source_file):

    def addAttribute(dic, attr, msgid, position, xml):
        if not xml:
            attr = attr.lower()
        if attr in dic:
            raise TALError(
                "attribute may only be specified once in i18n:attributes: "
                + attr,
                position)
        dic[attr] = msgid

    d = {}
    if ';' in i18nattrs:
        i18nattrlist = i18nattrs.split(';')
        i18nattrlist = [attr.strip().split() 
                        for attr in i18nattrlist if attr.strip()]
        for parts in i18nattrlist:
            if len(parts) > 2:
                raise TALError("illegal i18n:attributes specification: %r"
                                % parts, position)
            if len(parts) == 2:
                attr, msgid = parts
            else:
                # len(parts) == 1
                attr = parts[0]
                msgid = None
            addAttribute(d, attr, msgid, position, xml)
    else:
        i18nattrlist = i18nattrs.split()
        if len(i18nattrlist) == 1:
            addAttribute(d, i18nattrlist[0], None, position, xml)
        elif len(i18nattrlist) == 2:
            staticattrs = [attr[0] for attr in attrlist if len(attr) == 2]
            if (not i18nattrlist[1] in staticattrs) and (
                not i18nattrlist[1] in repldict):
                attr, msgid = i18nattrlist
                addAttribute(d, attr, msgid, position, xml)    
            else:
                import warnings
                warnings.warn(I18N_ATTRIBUTES_WARNING
                % (source_file, str(position), i18nattrs)
                , DeprecationWarning)
                msgid = None
                for attr in i18nattrlist:
                    addAttribute(d, attr, msgid, position, xml)    
        else:    
            import warnings
            warnings.warn(I18N_ATTRIBUTES_WARNING
            % (source_file, str(position), i18nattrs)
            , DeprecationWarning)
            msgid = None
            for attr in i18nattrlist:
                addAttribute(d, attr, msgid, position, xml)    
    return d

I18N_ATTRIBUTES_WARNING = (
    'Space separated attributes in i18n:attributes'
    ' are deprecated (i18n:attributes="value title"). Please use'
    ' semicolon to separate attributes'
    ' (i18n:attributes="value; title").'
    '\nFile %s at row, column %s\nAttributes %s')

def test():
    t = TALGenerator()
    t.pushProgram()
    t.emit("bar")
    p = t.popProgram()
    t.emit("foo", p)

if __name__ == "__main__":
    test()
