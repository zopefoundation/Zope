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
"""Interpreter for a pre-compiled TAL program.

$Id$
"""
import cgi
import sys
import getopt
import re
from cgi import escape

# Do not use cStringIO here!  It's not unicode aware. :(
from StringIO import StringIO
from DocumentTemplate.DT_Util import ustr
from ZODB.POSException import ConflictError

from zope.i18nmessageid import MessageID
from TALDefs import attrEscape, TAL_VERSION, METALError
from TALDefs import isCurrentVersion
from TALDefs import getProgramVersion, getProgramMode
from TALGenerator import TALGenerator
from TranslationContext import TranslationContext

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

def _init():
    d = {}
    for s in BOOLEAN_HTML_ATTRS:
        d[s] = 1
    return d

BOOLEAN_HTML_ATTRS = _init()

_nulljoin = ''.join
_spacejoin = ' '.join

def normalize(text):
    # Now we need to normalize the whitespace in implicit message ids and
    # implicit $name substitution values by stripping leading and trailing
    # whitespace, and folding all internal whitespace to a single space.
    return _spacejoin(text.split())


NAME_RE = r"[a-zA-Z][a-zA-Z0-9_]*"
_interp_regex = re.compile(r'(?<!\$)(\$(?:%(n)s|{%(n)s}))' %({'n': NAME_RE}))
_get_var_regex = re.compile(r'%(n)s' %({'n': NAME_RE}))

def interpolate(text, mapping):
    """Interpolate ${keyword} substitutions.

    This is called when no translation is provided by the translation
    service.
    """
    if not mapping:
        return text
    # Find all the spots we want to substitute.
    to_replace = _interp_regex.findall(text)
    # Now substitute with the variables in mapping.
    for string in to_replace:
        var = _get_var_regex.findall(string)[0]
        if mapping.has_key(var):
            # Call ustr because we may have an integer for instance.
            subst = ustr(mapping[var])
            try:
                text = text.replace(string, subst)
            except UnicodeError:
                # subst contains high-bit chars...
                # As we have no way of knowing the correct encoding,
                # substitue something instead of raising an exception.
                subst = `subst`[1:-1]
                text = text.replace(string, subst)
    return text


class AltTALGenerator(TALGenerator):

    def __init__(self, repldict, expressionCompiler=None, xml=0):
        self.repldict = repldict
        self.enabled = 1
        TALGenerator.__init__(self, expressionCompiler, xml)

    def enable(self, enabled):
        self.enabled = enabled

    def emit(self, *args):
        if self.enabled:
            TALGenerator.emit(self, *args)

    def emitStartElement(self, name, attrlist, taldict, metaldict, i18ndict,
                         position=(None, None), isend=0):
        metaldict = {}
        taldict = {}
        i18ndict = {}
        if self.enabled and self.repldict:
            taldict["attributes"] = "x x"
        TALGenerator.emitStartElement(self, name, attrlist,
                                      taldict, metaldict, i18ndict,
                                      position, isend)

    def replaceAttrs(self, attrlist, repldict):
        if self.enabled and self.repldict:
            repldict = self.repldict
            self.repldict = None
        return TALGenerator.replaceAttrs(self, attrlist, repldict)


class TALInterpreter:

    def __init__(self, program, macros, engine, stream=None,
                 debug=0, wrap=60, metal=1, tal=1, showtal=-1,
                 strictinsert=1, stackLimit=100, i18nInterpolate=1):
        self.program = program
        self.macros = macros
        self.engine = engine # Execution engine (aka context)
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
        self.position = None, None  # (lineno, offset)
        self.col = 0
        self.level = 0
        self.scopeLevel = 0
        self.sourceFile = None
        self.i18nStack = []
        self.i18nInterpolate = i18nInterpolate
        self.i18nContext = TranslationContext()

    def StringIO(self):
        # Third-party products wishing to provide a full Unicode-aware
        # StringIO can do so by monkey-patching this method.
        return FasterStringIO()

    def saveState(self):
        return (self.position, self.col, self.stream,
                self.scopeLevel, self.level, self.i18nContext)

    def restoreState(self, state):
        (self.position, self.col, self.stream,
         scopeLevel, level, i18n) = state
        self._stream_write = self.stream.write
        assert self.level == level
        while self.scopeLevel > scopeLevel:
            self.engine.endScope()
            self.scopeLevel = self.scopeLevel - 1
        self.engine.setPosition(self.position)
        self.i18nContext = i18n

    def restoreOutputState(self, state):
        (dummy, self.col, self.stream,
         scopeLevel, level, i18n) = state
        self._stream_write = self.stream.write
        assert self.level == level
        assert self.scopeLevel == scopeLevel

    def pushMacro(self, macroName, slots, entering=1):
        if len(self.macroStack) >= self.stackLimit:
            raise METALError("macro nesting limit (%d) exceeded "
                             "by %s" % (self.stackLimit, `macroName`))
        self.macroStack.append([macroName, slots, entering, self.i18nContext])

    def popMacro(self):
        return self.macroStack.pop()

    def __call__(self):
        assert self.level == 0
        assert self.scopeLevel == 0
        assert self.i18nContext.parent is None
        self.interpret(self.program)
        assert self.level == 0
        assert self.scopeLevel == 0
        assert self.i18nContext.parent is None
        if self.col > 0:
            self._stream_write("\n")
            self.col = 0

    def interpretWithStream(self, program, stream):
        oldstream = self.stream
        self.stream = stream
        self._stream_write = stream.write
        try:
            self.interpret(program)
        finally:
            self.stream = oldstream
            self._stream_write = oldstream.write

    def stream_write(self, s,
                     len=len):
        self._stream_write(s)
        i = s.rfind('\n')
        if i < 0:
            self.col = self.col + len(s)
        else:
            self.col = len(s) - (i + 1)

    bytecode_handlers = {}

    def interpret(self, program):
        oldlevel = self.level
        self.level = oldlevel + 1
        handlers = self.dispatch
        try:
            if self.debug:
                for (opcode, args) in program:
                    s = "%sdo_%s(%s)\n" % ("    "*self.level, opcode,
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
        self._currentTag = name
        L = ["<", name]
        append = L.append
        col = self.col + _len(name) + 1
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
                    # item[2] is the 'action' field:
                    if item[2] in ('metal', 'tal', 'xmlns', 'i18n'):
                        if not self.showtal:
                            continue
                        ok, name, s = self.attrAction(item)
                    else:
                        ok, name, s = attrAction(self, item)
                    if not ok:
                        continue
                slen = _len(s)
                if (wrap and
                    col >= align and
                    col + 1 + slen > wrap):
                    append("\n")
                    append(" "*align)
                    col = align + slen
                else:
                    append(" ")
                    col = col + 1 + slen
                append(s)
            append(end)
            col = col + endlen
        finally:
            self._stream_write(_nulljoin(L))
            self.col = col
    bytecode_handlers["startTag"] = do_startTag

    def attrAction(self, item):
        name, value, action = item[:3]
        if action == 'insert':
            return 0, name, value
        macs = self.macroStack
        if action == 'metal' and self.metal and macs:
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
                name = prefix + "fill-slot"
            elif suffix == "fill-slot":
                pass
            else:
                return 0, name, value

        if value is None:
            value = name
        else:
            value = '%s="%s"' % (name, attrEscape(value))
        return 1, name, value

    def attrAction_tal(self, item):
        name, value, action = item[:3]
        ok = 1
        expr, xlat, msgid = item[3:]
        if self.html and name.lower() in BOOLEAN_HTML_ATTRS:
            evalue = self.engine.evaluateBoolean(item[3])
            if evalue is self.Default:
                if action == 'insert': # Cancelled insert
                    ok = 0
            elif evalue:
                value = None
            else:
                ok = 0
        elif expr is not None:
            evalue = self.engine.evaluateText(item[3])
            if evalue is self.Default:
                if action == 'insert': # Cancelled insert
                    ok = 0
            else:
                if evalue is None:
                    ok = 0
                value = evalue
        else:
            evalue = None

        if ok:
            if xlat:
                translated = self.translate(msgid or value, value, {})
                if translated is not None:
                    value = translated
            if value is None:
                value = name
            elif evalue is self.Default:
                value = attrEscape(value)
            else:
                value = escape(value, quote=1)
            value = '%s="%s"' % (name, value)
        return ok, name, value
    bytecode_handlers["<attrAction>"] = attrAction

    def no_tag(self, start, program):
        state = self.saveState()
        self.stream = stream = self.StringIO()
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

    def do_rawtextBeginScope(self, (s, col, position, closeprev, dict)):
        self._stream_write(s)
        self.col = col
        self.position = position
        self.engine.setPosition(position)
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
        engine = self.engine
        self.position = position
        engine.setPosition(position)
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

    def do_beginI18nContext(self, settings):
        get = settings.get
        self.i18nContext = TranslationContext(self.i18nContext,
                                              domain=get("domain"),
                                              source=get("source"),
                                              target=get("target"))
    bytecode_handlers["beginI18nContext"] = do_beginI18nContext

    def do_endI18nContext(self, notused=None):
        self.i18nContext = self.i18nContext.parent
        assert self.i18nContext is not None
    bytecode_handlers["endI18nContext"] = do_endI18nContext

    def do_insertText(self, stuff):
        self.interpret(stuff[1])

    def do_insertText_tal(self, stuff):
        text = self.engine.evaluateText(stuff[0])
        if text is None:
            return
        if text is self.Default:
            self.interpret(stuff[1])
            return
        if isinstance(text, MessageID):
            # Translate this now.
            text = self.engine.translate(text.domain, text, text.mapping,
                                         default=text.default)
        s = escape(text)
        self._stream_write(s)
        i = s.rfind('\n')
        if i < 0:
            self.col = self.col + len(s)
        else:
            self.col = len(s) - (i + 1)
    bytecode_handlers["insertText"] = do_insertText

    def do_i18nVariable(self, stuff):
        varname, program, expression, structure = stuff
        if expression is None:
            # The value is implicitly the contents of this tag, so we have to
            # evaluate the mini-program to get the value of the variable.
            state = self.saveState()
            try:
                tmpstream = self.StringIO()
                self.interpretWithStream(program, tmpstream)
                if self.html and self._currentTag == "pre":
                    value = tmpstream.getvalue()
                else:
                    value = normalize(tmpstream.getvalue())
            finally:
                self.restoreState(state)
        else:
            # Evaluate the value to be associated with the variable in the
            # i18n interpolation dictionary.
            if structure:
                value = self.engine.evaluateStructure(expression)
            else:
                value = self.engine.evaluate(expression)

            # evaluate() does not do any I18n, so we do it here. 
            if isinstance(value, MessageID):
                # Translate this now.
                # XXX
                value = self.engine.translate(value.domain, value,
                                              value.mapping, value.default)

            if not structure:
                value = cgi.escape(ustr(value))

        # Either the i18n:name tag is nested inside an i18n:translate in which
        # case the last item on the stack has the i18n dictionary and string
        # representation, or the i18n:name and i18n:translate attributes are
        # in the same tag, in which case the i18nStack will be empty.  In that
        # case we can just output the ${name} to the stream
        i18ndict, srepr = self.i18nStack[-1]
        i18ndict[varname] = value
        placeholder = '${%s}' % varname
        srepr.append(placeholder)
        self._stream_write(placeholder)
    bytecode_handlers['i18nVariable'] = do_i18nVariable

    def do_insertTranslation(self, stuff):
        i18ndict = {}
        srepr = []
        obj = None
        self.i18nStack.append((i18ndict, srepr))
        msgid = stuff[0]
        # We need to evaluate the content of the tag because that will give us
        # several useful pieces of information.  First, the contents will
        # include an implicit message id, if no explicit one was given.
        # Second, it will evaluate any i18nVariable definitions in the body of
        # the translation (necessary for $varname substitutions).
        #
        # Use a temporary stream to capture the interpretation of the
        # subnodes, which should /not/ go to the output stream.
        currentTag = self._currentTag
        tmpstream = self.StringIO()
        self.interpretWithStream(stuff[1], tmpstream)
        # We only care about the evaluated contents if we need an implicit
        # message id.  All other useful information will be in the i18ndict on
        # the top of the i18nStack.
        default = tmpstream.getvalue()
        if not msgid:
            if self.html and currentTag == "pre":
                msgid = default
            else:
                msgid = normalize(default)
        self.i18nStack.pop()
        # See if there is was an i18n:data for msgid
        if len(stuff) > 2:
            obj = self.engine.evaluate(stuff[2])
        xlated_msgid = self.translate(msgid, default, i18ndict, obj)
        # XXX I can't decide whether we want to cgi escape the translated
        # string or not.  OT1H not doing this could introduce a cross-site
        # scripting vector by allowing translators to sneak JavaScript into
        # translations.  OTOH, for implicit interpolation values, we don't
        # want to escape stuff like ${name} <= "<b>Timmy</b>".
        assert xlated_msgid is not None
        self._stream_write(xlated_msgid)
    bytecode_handlers['insertTranslation'] = do_insertTranslation

    def do_insertStructure(self, stuff):
        self.interpret(stuff[2])

    def do_insertStructure_tal(self, (expr, repldict, block)):
        structure = self.engine.evaluateStructure(expr)
        if structure is None:
            return
        if structure is self.Default:
            self.interpret(block)
            return
        text = ustr(structure)
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
        gen = AltTALGenerator(repldict, self.engine.getCompiler(), 0)
        p = HTMLTALParser(gen) # Raises an exception if text is invalid
        p.parseString(text)
        program, macros = p.getCode()
        self.interpret(program)

    def insertXMLStructure(self, text, repldict):
        from TALParser import TALParser
        gen = AltTALGenerator(repldict, self.engine.getCompiler(), 0)
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

    def translate(self, msgid, default, i18ndict, obj=None):
        if obj:
            i18ndict.update(obj)
        if not self.i18nInterpolate:
            return msgid
        # XXX We need to pass in one of context or target_language
        return self.engine.translate(self.i18nContext.domain,
                                     msgid, i18ndict, default=default)

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
                assert macs[-1] is None
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
        prev_source = self.sourceFile
        self.interpret(macro)
        if self.sourceFile != prev_source:
            self.engine.setSourceFile(prev_source)
            self.sourceFile = prev_source
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
            macroName, slots = self.popMacro()[:2]
            slot = slots.get(slotName)
            if slot is not None:
                prev_source = self.sourceFile
                self.interpret(slot)
                if self.sourceFile != prev_source:
                    self.engine.setSourceFile(prev_source)
                    self.sourceFile = prev_source
                self.pushMacro(macroName, slots, entering=0)
                return
            self.pushMacro(macroName, slots)
            # Falling out of the 'if' allows the macro to be interpreted.
        self.interpret(block)
    bytecode_handlers["defineSlot"] = do_defineSlot

    def do_onError(self, (block, handler)):
        self.interpret(block)

    def do_onError_tal(self, (block, handler)):
        state = self.saveState()
        self.stream = stream = self.StringIO()
        self._stream_write = stream.write
        try:
            self.interpret(block)
        except ConflictError:
            raise
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


class FasterStringIO(StringIO):
    """Append-only version of StringIO.

    This let's us have a much faster write() method.
    """
    def close(self):
        if not self.closed:
            self.write = _write_ValueError
            StringIO.close(self)

    def seek(self, pos, mode=0):
        raise RuntimeError("FasterStringIO.seek() not allowed")

    def write(self, s):
        #assert self.pos == self.len
        self.buflist.append(s)
        self.len = self.pos = self.pos + len(s)


def _write_ValueError(s):
    raise ValueError, "I/O operation on closed file"
