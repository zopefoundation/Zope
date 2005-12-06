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
Common definitions used by TAL and METAL compilation an transformation.
"""

from types import ListType, TupleType

from ITALES import ITALESErrorInfo

TAL_VERSION = "1.5"

XML_NS = "http://www.w3.org/XML/1998/namespace" # URI for XML namespace
XMLNS_NS = "http://www.w3.org/2000/xmlns/" # URI for XML NS declarations

ZOPE_TAL_NS = "http://xml.zope.org/namespaces/tal"
ZOPE_METAL_NS = "http://xml.zope.org/namespaces/metal"
ZOPE_I18N_NS = "http://xml.zope.org/namespaces/i18n"

# This RE must exactly match the expression of the same name in the
# zope.i18n.simpletranslationservice module:
NAME_RE = "[a-zA-Z_][-a-zA-Z0-9_]*"

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

KNOWN_I18N_ATTRIBUTES = [
    "translate",
    "domain",
    "target",
    "source",
    "attributes",
    "data",
    "name",
    ]

class TALError(Exception):

    def __init__(self, msg, position=(None, None)):
        assert msg != ""
        self.msg = msg
        self.lineno = position[0]
        self.offset = position[1]
        self.filename = None

    def setFile(self, filename):
        self.filename = filename

    def __str__(self):
        result = self.msg
        if self.lineno is not None:
            result = result + ", at line %d" % self.lineno
        if self.offset is not None:
            result = result + ", column %d" % (self.offset + 1)
        if self.filename is not None:
            result = result + ', in file %s' % self.filename
        return result

class METALError(TALError):
    pass

class TALESError(TALError):
    pass

class I18NError(TALError):
    pass


class ErrorInfo:

    __implements__ = ITALESErrorInfo

    def __init__(self, err, position=(None, None)):
        if isinstance(err, Exception):
            self.type = err.__class__
            self.value = err
        else:
            self.type = err
            self.value = None
        self.lineno = position[0]
        self.offset = position[1]



import re
_attr_re = re.compile(r"\s*([^\s]+)\s+([^\s].*)\Z", re.S)
_subst_re = re.compile(r"\s*(?:(text|structure)\s+)?(.*)\Z", re.S)
del re

def parseAttributeReplacements(arg, xml):
    dict = {}
    for part in splitParts(arg):
        m = _attr_re.match(part)
        if not m:
            raise TALError("Bad syntax in attributes: " + `part`)
        name, expr = m.group(1, 2)
        if not xml:
            name = name.lower()
        if dict.has_key(name):
            raise TALError("Duplicate attribute name in attributes: " + `part`)
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
    arg = arg.replace(";;", "\0")
    parts = arg.split(';')
    parts = [p.replace("\0", ";") for p in parts]
    if len(parts) > 1 and not parts[-1].strip():
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
    if (len(program) >= 2 and
        isinstance(program[0], TupleType) and len(program[0]) == 2):
        opcode, version = program[0]
        if opcode == "version":
            return version
    return None

import re
_ent1_re = re.compile('&(?![A-Z#])', re.I)
_entch_re = re.compile('&([A-Z][A-Z0-9]*)(?![A-Z0-9;])', re.I)
_entn1_re = re.compile('&#(?![0-9X])', re.I)
_entnx_re = re.compile('&(#X[A-F0-9]*)(?![A-F0-9;])', re.I)
_entnd_re = re.compile('&(#[0-9][0-9]*)(?![0-9;])')
del re

def attrEscape(s):
    """Replace special characters '&<>' by character entities,
    except when '&' already begins a syntactically valid entity."""
    s = _ent1_re.sub('&amp;', s)
    s = _entch_re.sub(r'&amp;\1', s)
    s = _entn1_re.sub('&amp;#', s)
    s = _entnx_re.sub(r'&amp;\1', s)
    s = _entnd_re.sub(r'&amp;\1', s)
    s = s.replace('<', '&lt;')
    s = s.replace('>', '&gt;')
    s = s.replace('"', '&quot;')
    return s
