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
Dummy TALES engine so that I can test out the TAL implementation.
"""

import re
import string
from TALVisitor import NAME_RE

class DummyEngine:

    def __init__(self):
        dict = {}
        self.locals = self.globals = dict
        self.stack = [dict]

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
        m = re.match(r"(%s):(.*)" % NAME_RE, expression)
        if m:
            type, expr = m.group(1, 2)
        else:
            type = "var"
            expr = expression
        if type == "str":
            return expr
        if type == "local":
            return self.locals[string.strip(expr)]
        if type == "global":
            return self.globals[string.strip(expr)]
        if type == "var":
            expr = string.strip(expr)
            if self.locals.has_key(expr):
                return self.locals[expr]
            else:
                return self.globals[expr]
        if type == "python":
            return eval(expr, self.globals, self.locals)
        print "Unrecognized expression:", `expression`
        return None

    def evaluateValue(self, expr):
        return self.evaluate(expr)

    def evaluateBoolean(self, expr):
        return self.evaluate(expr)

    def evaluateText(self, expr):
        text = self.evaluate(expr)
        if text is not None:
            text = str(text)
        return text

    def evaluateStructure(self, expr):
        # XXX Should return None or a DOM tree
        return self.evaluate(expr)

    def evaluateSequence(self, expr):
        # XXX Should return a sequence
        return self.evaluate(expr)

    def findMacroDocument(self, macroName):
        if not macroName:
            print "Empty macro name:", macroName
            return None, None
        i = string.rfind(macroName, '/')
        if i < 0:
            # No slash -- must be a locally defined macro
            return None, macroName
        else:
            # Up to last slash is the filename
            fileName = macroName[:i]
            from Products.ParsedXML.DOM import ExpatBuilder
            doc = ExpatBuilder.parse(fileName, 1)
            return doc, macroName[i+1:]

    def setupLoop(self, name, expr):
        seq = self.evaluateSequence(expr)
        return Iterator(name, seq, self)

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
