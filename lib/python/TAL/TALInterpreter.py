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
Interpreter for a pre-compiled TAL program.
"""

import sys
import getopt
import cgi

from string import join, lower, rfind
try:
    from strop import lower, rfind
except ImportError:
    pass

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
            taldict["attributes"] = ""
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
        self.TALESError = engine.getTALESError()
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

    def saveState(self):
        return (self.position, self.col, self.stream,
                self.scopeLevel, self.level)

    def restoreState(self, state):
        (self.position, self.col, self.stream, scopeLevel, level) = state
        self._stream_write = self.stream.write
        assert self.level == level
        while self.scopeLevel > scopeLevel:
            self.do_endScope()

    def restoreOutputState(self, state):
        (dummy, self.col, self.stream, scopeLevel, level) = state
        self._stream_write = self.stream.write
        assert self.level == level
        assert self.scopeLevel == scopeLevel

    def pushMacro(self, what, macroName, slots):
        if len(self.macroStack) >= self.stackLimit:
            raise METALError("macro nesting limit (%d) exceeded "
                             "by %s %s" % (self.stackLimit, what, `macroName`))
        self.macroStack.append((what, macroName, slots))

    def popMacro(self):
        return self.macroStack.pop()

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
                     len=len, rfind=rfind):
        self._stream_write(s)
        i = rfind(s, '\n')
        if i < 0:
            self.col = self.col + len(s)
        else:
            self.col = len(s) - (i + 1)

    bytecode_handlers = {}

    def interpret(self, program):
        self.level = self.level + 1
        handlers = self.dispatch
        _apply = apply
        _tuple = tuple
        tup = (self,)
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
            self.level = self.level - 1
            del tup

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

    def do_setPosition(self, position):
        self.position = position
    bytecode_handlers["setPosition"] = do_setPosition

    def do_startEndTag(self, stuff):
        self.do_startTag(stuff, self.endsep, self.endlen)
    bytecode_handlers["startEndTag"] = do_startEndTag

    def do_startTag(self, (name, attrList),
                    end=">", endlen=1, _len=len, _quote=quote):
        # The bytecode generator does not cause calls to this method
        # for start tags with no attributes; those are optimized down
        # to rawtext events.  Hence, there is no special "fast path"
        # for that case.
        _stream_write = self._stream_write
        _stream_write("<" + name)
        namelen = _len(name)
        col = self.col + namelen + 1
        wrap = self.wrap
        align = col + 1 + namelen
        if align >= wrap/2:
            align = 4  # Avoid a narrow column far to the right
        try:
            for item in attrList:
                if _len(item) == 2:
                    name, s = item
                else:
                    ok, name, value = self.attrAction(item)
                    if not ok:
                        continue
                    if value is None:
                        s = name
                    else:
                        s = "%s=%s" % (name, _quote(value))
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
        if not self.showtal and action > 1:
            return 0, name, value
        ok = 1
        if action <= 1 and self.tal:
            if self.html and lower(name) in BOOLEAN_HTML_ATTRS:
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
        elif action == 2 and self.metal:
            i = rfind(name, ":") + 1
            prefix, suffix = name[:i], name[i:]
            ##self.dumpMacroStack(prefix, suffix, value)
            what, macroName, slots = self.macroStack[-1]
            if suffix == "define-macro":
                if what == "use-macro":
                    name = prefix + "use-macro"
                    value = macroName
                else:
                    assert what == "define-macro"
                    i = self.macroContext("use-macro")
                    if i >= 0:
                        j = self.macroContext("define-slot")
                        if j > i:
                            name = prefix + "use-macro"
                        else:
                            ok = 0
            elif suffix == "define-slot":
                assert what == "define-slot"
                if self.macroContext("use-macro") >= 0:
                    name = prefix + "fill-slot"

        elif action == 1: # Unexecuted insert
            ok = 0
        return ok, name, value

    def dumpMacroStack(self, prefix, suffix, value):
        sys.stderr.write("+---- %s%s = %s\n" % (prefix, suffix, value))
        for i in range(len(self.macroStack)):
            what, macroName, slots = self.macroStack[i]
            sys.stderr.write("| %2d. %-12s %-12s %s\n" %
                             (i, what, macroName, slots and slots.keys()))
        sys.stderr.write("+--------------------------------------\n")

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

    def do_setLocal(self, junk):
        pass

    def do_setLocal_tal(self, (name, expr)):
        value = self.engine.evaluateValue(expr)
        self.engine.setLocal(name, value)
    bytecode_handlers["setLocal"] = do_setLocal

    def do_setGlobal_tal(self, (name, expr)):
        value = self.engine.evaluateValue(expr)
        self.engine.setGlobal(name, value)
    bytecode_handlers["setGlobal"] = do_setLocal

    def do_insertText(self, (expr, block)):
        self.interpret(block)

    def do_insertText_tal(self, (expr, block)):
        text = self.engine.evaluateText(expr)
        if text is None:
            return
        if text is self.Default:
            self.interpret(block)
            return
        self.stream_write(cgi.escape(text))
    bytecode_handlers["insertText"] = do_insertText

    def do_insertStructure(self, (expr, repldict, block)):
        if not self.tal:
            self.interpret(block)
            return
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
        if not self.metal:
            self.interpret(macro)
            return
        self.pushMacro("define-macro", macroName, None)
        self.interpret(macro)
        self.popMacro()
    bytecode_handlers["defineMacro"] = do_defineMacro

    def do_useMacro(self, (macroName, macroExpr, compiledSlots, block)):
        if not self.metal:
            self.interpret(block)
            return
        macro = self.engine.evaluateMacro(macroExpr)
        if macro is self.Default:
            self.interpret(block)
            return
        if not isCurrentVersion(macro):
            raise METALError("macro %s has incompatible version %s" %
                             (`macroName`, `getProgramVersion(macro)`),
                             self.position)
        mode = getProgramMode(macro)
        if mode != (self.html and "html" or "xml"):
            raise METALError("macro %s has incompatible mode %s" %
                             (`macroName`, `mode`), self.position)
        self.pushMacro("use-macro", macroName, compiledSlots)
        self.interpret(macro)
        self.popMacro()
    bytecode_handlers["useMacro"] = do_useMacro

    def do_fillSlot(self, (slotName, block)):
        if not self.metal:
            self.interpret(block)
            return
        self.pushMacro("fill-slot", slotName, None)
        self.interpret(block)
        self.popMacro()
    bytecode_handlers["fillSlot"] = do_fillSlot

    def do_defineSlot(self, (slotName, block)):
        if not self.metal:
            self.interpret(block)
            return
        slot = None
        for what, macroName, slots in self.macroStack:
            if what == "use-macro" and slots is not None:
                slot = slots.get(slotName, slot)
        self.pushMacro("define-slot", slotName, None)
        if slot:
            self.interpret(slot)
        else:
            self.interpret(block)
        self.popMacro()
    bytecode_handlers["defineSlot"] = do_defineSlot

    def do_onError(self, (block, handler)):
        self.interpret(block)

    def do_onError_tal(self, (block, handler)):
        state = self.saveState()
        self.stream = stream = StringIO()
        self._stream_write = stream.write
        try:
            self.interpret(block)
        except self.TALESError, err:
            self.restoreState(state)
            engine = self.engine
            engine.beginScope()
            err.lineno, err.offset = self.position
            engine.setLocal('error', err)
            self.interpret(handler)
            engine.endScope()
        else:
            self.restoreOutputState(state)
            self.stream_write(stream.getvalue())
    bytecode_handlers["onError"] = do_onError

    bytecode_handlers_tal = bytecode_handlers.copy()
    bytecode_handlers_tal["beginScope"] = do_beginScope_tal
    bytecode_handlers_tal["setLocal"] = do_setLocal_tal
    bytecode_handlers_tal["setGlobal"] = do_setGlobal_tal
    bytecode_handlers_tal["insertText"] = do_insertText_tal
    bytecode_handlers_tal["loop"] = do_loop_tal
    bytecode_handlers_tal["onError"] = do_onError_tal


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
