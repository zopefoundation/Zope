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
Common definitions used by TAL and METAL compilation an transformation.
"""

from types import ListType, TupleType

TAL_VERSION = "1.3.2"

XML_NS = "http://www.w3.org/XML/1998/namespace" # URI for XML namespace
XMLNS_NS = "http://www.w3.org/2000/xmlns/" # URI for XML NS declarations

ZOPE_TAL_NS = "http://xml.zope.org/namespaces/tal"
ZOPE_METAL_NS = "http://xml.zope.org/namespaces/metal"

NAME_RE = "[a-zA-Z_][a-zA-Z0-9_]*"

KNOWN_METAL_ATTRIBUTES = [
    "define-macro",
    "use-macro",
    "define-slot",
    "fill-slot",
    "slot",
    ]

KNOWN_TAL_ATTRIBUTES = [
    "define",
    "condition",
    "content",
    "replace",
    "repeat",
    "attributes",
    "on-error",
    "omit-tag",
    "tal tag",
    ]

class TALError(Exception):

    def __init__(self, msg, position=(None, None)):
        assert msg != ""
        self.msg = msg
        self.lineno = position[0]
        self.offset = position[1]

    def __str__(self):
        result = self.msg
        if self.lineno is not None:
            result = result + ", at line %d" % self.lineno
        if self.offset is not None:
            result = result + ", column %d" % (self.offset + 1)
        return result

class METALError(TALError):
    pass

class TALESError(TALError):

    # This exception can carry around another exception + traceback

    def takeTraceback(self):
        t = self.info[2]
        self.info = self.info[:2] + (None,)
        return t

    def __init__(self, msg, position=(None, None), info=(None, None, None)):
        t, v, tb = info
        if t:
            if issubclass(t, Exception) and t.__module__ == "exceptions":
                err = t.__name__
            else:
                err = str(t)
            v = v is not None and str(v)
            if v:
                err = "%s: %s" % (err, v)
            msg = "%s: %s" % (msg, err)
        TALError.__init__(self, msg, position)
        self.info = info

import re
_attr_re = re.compile(r"\s*([^\s]+)\s+([^\s].*)\Z", re.S)
_subst_re = re.compile(r"\s*(?:(text|structure)\s+)?(.*)\Z", re.S)
del re

def parseAttributeReplacements(arg):
    dict = {}
    for part in splitParts(arg):
        m = _attr_re.match(part)
        if not m:
            raise TALError("Bad syntax in attributes:" + `part`)
        name, expr = m.group(1, 2)
        if dict.has_key(name):
            raise TALError("Duplicate attribute name in attributes:" + `part`)
        dict[name] = expr
    return dict

def parseSubstitution(arg, position=(None, None)):
    m = _subst_re.match(arg)
    if not m:
        raise TALError("Bad syntax in substitution text: " + `arg`, position)
    key, expr = m.group(1, 2)
    if not key:
        key = "text"
    return key, expr

def splitParts(arg):
    # Break in pieces at undoubled semicolons and
    # change double semicolons to singles:
    import string
    arg = string.replace(arg, ";;", "\0")
    parts = string.split(arg, ';')
    parts = map(lambda s, repl=string.replace: repl(s, "\0", ";"), parts)
    if len(parts) > 1 and not string.strip(parts[-1]):
        del parts[-1] # It ended in a semicolon
    return parts

def isCurrentVersion(program):
    version = getProgramVersion(program)
    return version == TAL_VERSION

def getProgramMode(program):
    version = getProgramVersion(program)
    if (version == TAL_VERSION and isinstance(program[1], TupleType) and
        len(program[1]) == 2):
        opcode, mode = program[1]
        if opcode == "mode":
            return mode
    return None

def getProgramVersion(program):
    if (isinstance(program, ListType) and len(program) >= 2 and
        isinstance(program[0], TupleType) and len(program[0]) == 2):
        opcode, version = program[0]
        if opcode == "version":
            return version
    return None

import cgi
def quote(s, escape=cgi.escape):
    return '"%s"' % escape(s, 1)
del cgi
