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
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Interpreter for a pre-compiled TAL program.
"""

import sys
import getopt

from cgi import escape

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from TALDefs import quote, TAL_VERSION, TALError, METALError
from TALDefs import isCurrentVersion, getProgramVersion, getProgramMode
from TALGenerator import TALGenerator

BOOLEAN_HTML_ATTRS = [
    # List of Boolean attributes in HTML that should be rendered in
    # minimized form (e.g. <img ismap> rather than <img ismap="">)
    # From http://www.w3.org/TR/xhtml1/#guidelines (C.10)
    # XXX The problem with this is that this is not valid XML and
    # can't be parsed back!
    "compact", "nowrap", "ismap", "declare", "noshade", "checked",
    "disabled", "readonly", "multiple", "selected", "noresize",
    "defer"
]

EMPTY_HTML_TAGS = [
    # List of HTML tags with an empty content model; these are
    # rendered in minimized form, e.g. <img />.
    # From http://www.w3.org/TR/xhtml1/#dtds
    "base", "meta", "link", "hr", "br", "param", "img", "area",
    "input", "col", "basefont", "isindex", "frame",
]

class AltTALGenerator(TALGenerator):

    def __init__(self, repldict, expressionCompiler=None, xml=0):
        self.repldict = repldict
        self.enabled = 1
        TALGenerator.__init__(self, expressionCompiler, xml)

    def enable(self, enabled):
        self.enabled = enabled

    def emit(self, *args):
        if self.enabled:
            apply(TALGenerator.emit, (self,) + args)

    def emitStartElement(self, name, attrlist, taldict, metaldict,
                         position=(None, None), isend=0):
        metaldict = {}
        taldict = {}
        if self.enabled and self.repldict:
            taldict["attributes"] = "x x"
        TALGenerator.emitStartElement(self, name, attrlist,
                                      taldict, metaldict, position, isend)

    def replaceAttrs(self, attrlist, repldict):
        if self.enabled and self.repldict:
            repldict = self.repldict
            self.repldict = None
        return TALGenerator.replaceAttrs(self, attrlist, repldict)


class TALInterpreter:

    def __init__(self, program, macros, engine, stream=None,
                 debug=0, wrap=60, metal=1, tal=1, showtal=-1,
                 strictinsert=1, stackLimit=100):
        self.program = program
        self.macros = macros
        self.engine = engine
        self.Default = engine.getDefault()
        self.stream = stream or sys.stdout
        self._stream_write = self.stream.write
        self.debug = debug
        self.wrap = wrap
        self.metal = metal
        self.tal = tal
        if tal:
            self.dispatch = self.bytecode_handlers_tal
        else:
            self.dispatch = self.bytecode_handlers
        assert showtal in (-1, 0, 1)
        if showtal == -1:
            showtal = (not tal)
        self.showtal = showtal
        self.strictinsert = strictinsert
        self.stackLimit = stackLimit
        self.html = 0
        self.endsep = "/>"
        self.endlen = len(self.endsep)
        self.macroStack = []
        self.popMacro = self.macroStack.pop
        self.position = None, None  # (lineno, offset)
        self.col = 0
        self.level = 0
        self.scopeLevel = 0
        self.sourceFile = None

    def saveState(self):
        return (self.position, self.col, self.stream,
                self.scopeLevel, self.level)

    def restoreState(self, state):
        (self.position, self.col, self.stream, scopeLevel, level) = state
        self._stream_write = self.stream.write
        assert self.level == level
        while self.scopeLevel > scopeLevel:
            self.engine.endScope()
            self.scopeLevel = self.scopeLevel - 1
        self.engine.setPosition(self.position)

    def restoreOutputState(self, state):
        (dummy, self.col, self.stream, scopeLevel, level) = state
        self._stream_write = self.stream.write
        assert self.level == level
        assert self.scopeLevel == scopeLevel

    def pushMacro(self, macroName, slots, entering=1):
        if len(self.macroStack) >= self.stackLimit:
            raise METALError("macro nesting limit (%d) exceeded "
                             "by %s" % (self.stackLimit, `macroName`))
        self.macroStack.append([macroName, slots, entering])

    def macroContext(self, what):
        macroStack = self.macroStack
        i = len(macroStack)
        while i > 0:
            i = i-1
            if macroStack[i][0] == what:
                return i
        return -1

    def __call__(self):
        assert self.level == 0
        assert self.scopeLevel == 0
        self.interpret(self.program)
        assert self.level == 0
        assert self.scopeLevel == 0
        if self.col > 0:
            self._stream_write("\n")
            self.col = 0

    def stream_write(self, s,
                     len=len):
        self._stream_write(s)
        i = s.rfind('\n')
        if i < 0:
            self.col = self.col + len(s)
        else:
            self.col = len(s) - (i + 1)

    bytecode_handlers = {}

    def interpret(self, program, None=None):
        oldlevel = self.level
        self.level = oldlevel + 1
        handlers = self.dispatch
        try:
            if self.debug:
                for (opcode, args) in program:
                    s = "%sdo_%s%s\n" % ("    "*self.level, opcode,
                                      repr(args))
                    if len(s) > 80:
                        s = s[:76] + "...\n"
                    sys.stderr.write(s)
                    handlers[opcode](self, args)
            else:
                for (opcode, args) in program:
                    handlers[opcode](self, args)
        finally:
            self.level = oldlevel

    def do_version(self, version):
        assert version == TAL_VERSION
    bytecode_handlers["version"] = do_version

    def do_mode(self, mode):
        assert mode in ("html", "xml")
        self.html = (mode == "html")
        if self.html:
            self.endsep = " />"
        else:
            self.endsep = "/>"
        self.endlen = len(self.endsep)
    bytecode_handlers["mode"] = do_mode

    def do_setSourceFile(self, source_file):
        self.sourceFile = source_file
        self.engine.setSourceFile(source_file)
    bytecode_handlers["setSourceFile"] = do_setSourceFile

    def do_setPosition(self, position):
        self.position = position
        self.engine.setPosition(position)
    bytecode_handlers["setPosition"] = do_setPosition

    def do_startEndTag(self, stuff):
        self.do_startTag(stuff, self.endsep, self.endlen)
    bytecode_handlers["startEndTag"] = do_startEndTag

    def do_startTag(self, (name, attrList),
                    end=">", endlen=1, _len=len):
        # The bytecode generator does not cause calls to this method
        # for start tags with no attributes; those are optimized down
        # to rawtext events.  Hence, there is no special "fast path"
        # for that case.
        _stream_write = self._stream_write
        _stream_write("<" + name)
        namelen = _len(name)
        col = self.col + namelen + 1
        wrap = self.wrap
        align = col + 1
        if align >= wrap/2:
            align = 4  # Avoid a narrow column far to the right
        attrAction = self.dispatch["<attrAction>"]
        try:
            for item in attrList:
                if _len(item) == 2:
                    name, s = item
                else:
                    ok, name, s = attrAction(self, item)
                    if not ok:
                        continue
                slen = _len(s)
                if (wrap and
                    col >= align and
                    col + 1 + slen > wrap):
                    _stream_write("\n" + " "*align)
                    col = align + slen
                else:
                    s = " " + s
                    col = col + 1 + slen
                _stream_write(s)
            _stream_write(end)
            col = col + endlen
        finally:
            self.col = col
    bytecode_handlers["startTag"] = do_startTag

    def attrAction(self, item):
        name, value, action = item[:3]
        if action == 1 or (action > 1 and not self.showtal):
            return 0, name, value
        macs = self.macroStack
        if action == 2 and self.metal and macs:
            if len(macs) > 1 or not macs[-1][2]:
                # Drop all METAL attributes at a use-depth above one.
                return 0, name, value
            # Clear 'entering' flag
            macs[-1][2] = 0
            # Convert or drop depth-one METAL attributes.
            i = name.rfind(":") + 1
            prefix, suffix = name[:i], name[i:]
            if suffix == "define-macro":
                # Convert define-macro as we enter depth one.
                name = prefix + "use-macro"
                value = macs[-1][0] # Macro name
            elif suffix == "define-slot":
                name = prefix + "slot"
            elif suffix == "fill-slot":
                pass
            else:
                return 0, name, value

        if value is None:
            value = name
        else:
            value = "%s=%s" % (name, quote(value))
        return 1, name, value

    def attrAction_tal(self, item):
        name, value, action = item[:3]
        if action > 1:
            return self.attrAction(item)
        ok = 1
        if self.html and name.lower() in BOOLEAN_HTML_ATTRS:
            evalue = self.engine.evaluateBoolean(item[3])
            if evalue is self.Default:
                if action == 1: # Cancelled insert
                    ok = 0
            elif evalue:
                value = None
            else:
                ok = 0
        else:
            evalue = self.engine.evaluateText(item[3])
            if evalue is self.Default:
                if action == 1: # Cancelled insert
                    ok = 0
            else:
                if evalue is None:
                    ok = 0
                value = evalue
        if ok:
            if value is None:
                value = name
            value = "%s=%s" % (name, quote(value))
        return ok, name, value

    bytecode_handlers["<attrAction>"] = attrAction

    def no_tag(self, start, program):
        state = self.saveState()
        self.stream = stream = StringIO()
        self._stream_write = stream.write
        self.interpret(start)
        self.restoreOutputState(state)
        self.interpret(program)

    def do_optTag(self, (name, cexpr, tag_ns, isend, start, program),
                  omit=0):
        if tag_ns and not self.showtal:
            return self.no_tag(start, program)

        self.interpret(start)
        if not isend:
            self.interpret(program)
            s = '</%s>' % name
            self._stream_write(s)
            self.col = self.col + len(s)

    def do_optTag_tal(self, stuff):
        cexpr = stuff[1]
        if cexpr is not None and (cexpr == '' or
                                  self.engine.evaluateBoolean(cexpr)):
            self.no_tag(stuff[-2], stuff[-1])
        else:
            self.do_optTag(stuff)
    bytecode_handlers["optTag"] = do_optTag

    def dumpMacroStack(self, prefix, suffix, value):
        sys.stderr.write("+---- %s%s = %s\n" % (prefix, suffix, value))
        for i in range(len(self.macroStack)):
            what, macroName, slots = self.macroStack[i]
            sys.stderr.write("| %2d. %-12s %-12s %s\n" %
                             (i, what, macroName, slots and slots.keys()))
        sys.stderr.write("+--------------------------------------\n")

    def do_rawtextBeginScope(self, (s, col, position, closeprev, dict)):
        self._stream_write(s)
        self.col = col
        self.do_setPosition(position)
        if closeprev:
            engine = self.engine
            engine.endScope()
            engine.beginScope()
        else:
            self.engine.beginScope()
            self.scopeLevel = self.scopeLevel + 1

    def do_rawtextBeginScope_tal(self, (s, col, position, closeprev, dict)):
        self._stream_write(s)
        self.col = col
        self.do_setPosition(position)
        engine = self.engine
        if closeprev:
            engine.endScope()
            engine.beginScope()
        else:
            engine.beginScope()
            self.scopeLevel = self.scopeLevel + 1
        engine.setLocal("attrs", dict)
    bytecode_handlers["rawtextBeginScope"] = do_rawtextBeginScope

    def do_beginScope(self, dict):
        self.engine.beginScope()
        self.scopeLevel = self.scopeLevel + 1

    def do_beginScope_tal(self, dict):
        engine = self.engine
        engine.beginScope()
        engine.setLocal("attrs", dict)
        self.scopeLevel = self.scopeLevel + 1
    bytecode_handlers["beginScope"] = do_beginScope

    def do_endScope(self, notused=None):
        self.engine.endScope()
        self.scopeLevel = self.scopeLevel - 1
    bytecode_handlers["endScope"] = do_endScope

    def do_setLocal(self, notused):
        pass

    def do_setLocal_tal(self, (name, expr)):
        self.engine.setLocal(name, self.engine.evaluateValue(expr))
    bytecode_handlers["setLocal"] = do_setLocal

    def do_setGlobal_tal(self, (name, expr)):
        self.engine.setGlobal(name, self.engine.evaluateValue(expr))
    bytecode_handlers["setGlobal"] = do_setLocal

    def do_insertText(self, stuff):
        self.interpret(stuff[1])

    def do_insertText_tal(self, stuff):
        text = self.engine.evaluateText(stuff[0])
        if text is None:
            return
        if text is self.Default:
            self.interpret(stuff[1])
            return
        s = escape(text)
        self._stream_write(s)
        i = s.rfind('\n')
        if i < 0:
            self.col = self.col + len(s)
        else:
            self.col = len(s) - (i + 1)
    bytecode_handlers["insertText"] = do_insertText

    def do_insertStructure(self, stuff):
        self.interpret(stuff[2])

    def do_insertStructure_tal(self, (expr, repldict, block)):
        structure = self.engine.evaluateStructure(expr)
        if structure is None:
            return
        if structure is self.Default:
            self.interpret(block)
            return
        text = str(structure)
        if not (repldict or self.strictinsert):
            # Take a shortcut, no error checking
            self.stream_write(text)
            return
        if self.html:
            self.insertHTMLStructure(text, repldict)
        else:
            self.insertXMLStructure(text, repldict)
    bytecode_handlers["insertStructure"] = do_insertStructure

    def insertHTMLStructure(self, text, repldict):
        from HTMLTALParser import HTMLTALParser
        gen = AltTALGenerator(repldict, self.engine, 0)
        p = HTMLTALParser(gen) # Raises an exception if text is invalid
        p.parseString(text)
        program, macros = p.getCode()
        self.interpret(program)

    def insertXMLStructure(self, text, repldict):
        from TALParser import TALParser
        gen = AltTALGenerator(repldict, self.engine, 0)
        p = TALParser(gen)
        gen.enable(0)
        p.parseFragment('<!DOCTYPE foo PUBLIC "foo" "bar"><foo>')
        gen.enable(1)
        p.parseFragment(text) # Raises an exception if text is invalid
        gen.enable(0)
        p.parseFragment('</foo>', 1)
        program, macros = gen.getCode()
        self.interpret(program)

    def do_loop(self, (name, expr, block)):
        self.interpret(block)

    def do_loop_tal(self, (name, expr, block)):
        iterator = self.engine.setRepeat(name, expr)
        while iterator.next():
            self.interpret(block)
    bytecode_handlers["loop"] = do_loop

    def do_rawtextColumn(self, (s, col)):
        self._stream_write(s)
        self.col = col
    bytecode_handlers["rawtextColumn"] = do_rawtextColumn

    def do_rawtextOffset(self, (s, offset)):
        self._stream_write(s)
        self.col = self.col + offset
    bytecode_handlers["rawtextOffset"] = do_rawtextOffset

    def do_condition(self, (condition, block)):
        if not self.tal or self.engine.evaluateBoolean(condition):
            self.interpret(block)
    bytecode_handlers["condition"] = do_condition

    def do_defineMacro(self, (macroName, macro)):
        macs = self.macroStack
        if len(macs) == 1:
            entering = macs[-1][2]
            if not entering:
                macs.append(None)
                self.interpret(macro)
                macs.pop()
                return
        self.interpret(macro)
    bytecode_handlers["defineMacro"] = do_defineMacro

    def do_useMacro(self, (macroName, macroExpr, compiledSlots, block)):
        if not self.metal:
            self.interpret(block)
            return
        macro = self.engine.evaluateMacro(macroExpr)
        if macro is self.Default:
            macro = block
        else:
            if not isCurrentVersion(macro):
                raise METALError("macro %s has incompatible version %s" %
                                 (`macroName`, `getProgramVersion(macro)`),
                                 self.position)
            mode = getProgramMode(macro)
            if mode != (self.html and "html" or "xml"):
                raise METALError("macro %s has incompatible mode %s" %
                                 (`macroName`, `mode`), self.position)
        self.pushMacro(macroName, compiledSlots)
        saved_source = self.sourceFile
        saved_position = self.position  # Used by Boa Constructor
        self.interpret(macro)
        if self.sourceFile != saved_source:
            self.engine.setSourceFile(saved_source)
            self.sourceFile = saved_source
        self.popMacro()
    bytecode_handlers["useMacro"] = do_useMacro

    def do_fillSlot(self, (slotName, block)):
        # This is only executed if the enclosing 'use-macro' evaluates
        # to 'default'.
        self.interpret(block)
    bytecode_handlers["fillSlot"] = do_fillSlot

    def do_defineSlot(self, (slotName, block)):
        if not self.metal:
            self.interpret(block)
            return
        macs = self.macroStack
        if macs and macs[-1] is not None:
            saved_source = self.sourceFile
            saved_position = self.position  # Used by Boa Constructor
            macroName, slots = self.popMacro()[:2]
            slot = slots.get(slotName)
            if slot is not None:
                self.interpret(slot)
                if self.sourceFile != saved_source:
                    self.engine.setSourceFile(saved_source)
                    self.sourceFile = saved_source
                self.pushMacro(macroName, slots, entering=0)
                return
            self.pushMacro(macroName, slots)
            if len(macs) == 1:
                self.interpret(block)
                return
        self.interpret(block)
    bytecode_handlers["defineSlot"] = do_defineSlot

    def do_onError(self, (block, handler)):
        self.interpret(block)

    def do_onError_tal(self, (block, handler)):
        state = self.saveState()
        self.stream = stream = StringIO()
        self._stream_write = stream.write
        try:
            self.interpret(block)
        except:
            exc = sys.exc_info()[1]
            self.restoreState(state)
            engine = self.engine
            engine.beginScope()
            error = engine.createErrorInfo(exc, self.position)
            engine.setLocal('error', error)
            try:
                self.interpret(handler)
            finally:
                engine.endScope()
        else:
            self.restoreOutputState(state)
            self.stream_write(stream.getvalue())
    bytecode_handlers["onError"] = do_onError

    bytecode_handlers_tal = bytecode_handlers.copy()
    bytecode_handlers_tal["rawtextBeginScope"] = do_rawtextBeginScope_tal
    bytecode_handlers_tal["beginScope"] = do_beginScope_tal
    bytecode_handlers_tal["setLocal"] = do_setLocal_tal
    bytecode_handlers_tal["setGlobal"] = do_setGlobal_tal
    bytecode_handlers_tal["insertStructure"] = do_insertStructure_tal
    bytecode_handlers_tal["insertText"] = do_insertText_tal
    bytecode_handlers_tal["loop"] = do_loop_tal
    bytecode_handlers_tal["onError"] = do_onError_tal
    bytecode_handlers_tal["<attrAction>"] = attrAction_tal
    bytecode_handlers_tal["optTag"] = do_optTag_tal


def test():
    from driver import FILE, parsefile
    from DummyEngine import DummyEngine
    try:
        opts, args = getopt.getopt(sys.argv[1:], "")
    except getopt.error, msg:
        print msg
        sys.exit(2)
    if args:
        file = args[0]
    else:
        file = FILE
    doc = parsefile(file)
    compiler = TALCompiler(doc)
    program, macros = compiler()
    engine = DummyEngine()
    interpreter = TALInterpreter(program, macros, engine)
    interpreter()

if __name__ == "__main__":
    test()
