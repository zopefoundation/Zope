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
Parse HTML and compile to TALInterpreter intermediate code.
"""

import sys
import string

from TALGenerator import TALGenerator
from TALDefs import ZOPE_METAL_NS, ZOPE_TAL_NS, METALError, TALError
from HTMLParser import HTMLParser, HTMLParseError

BOOLEAN_HTML_ATTRS = [
    # List of Boolean attributes in HTML that may be given in
    # minimized form (e.g. <img ismap> rather than <img ismap="">)
    # From http://www.w3.org/TR/xhtml1/#guidelines (C.10)
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

PARA_LEVEL_HTML_TAGS = [
    # List of HTML elements that close open paragraph-level elements
    # and are themselves paragraph-level.
    "h1", "h2", "h3", "h4", "h5", "h6", "p",
    ]

BLOCK_CLOSING_TAG_MAP = {
    "tr": ("tr", "td", "th"),
    "td": ("td", "th"),
    "th": ("td", "th"),
    "li": ("li",),
    "dd": ("dd", "dt"),
    "dt": ("dd", "dt"),
    }

BLOCK_LEVEL_HTML_TAGS = [
    # List of HTML tags that denote larger sections than paragraphs.
    "blockquote", "table", "tr", "th", "td", "thead", "tfoot", "tbody",
    "noframe", "ul", "ol", "li", "dl", "dt", "dd", "div",
    ]

TIGHTEN_IMPLICIT_CLOSE_TAGS = (PARA_LEVEL_HTML_TAGS
                               + BLOCK_CLOSING_TAG_MAP.keys())


class NestingError(HTMLParseError):
    """Exception raised when elements aren't properly nested."""

    def __init__(self, tagstack, endtag, position=(None, None)):
        self.endtag = endtag
        if tagstack:
            if len(tagstack) == 1:
                msg = ('Open tag <%s> does not match close tag </%s>'
                       % (tagstack[0], endtag))
            else:
                msg = ('Open tags <%s> do not match close tag </%s>'
                       % (string.join(tagstack, '>, <'), endtag))
        else:
            msg = 'No tags are open to match </%s>' % endtag
        HTMLParseError.__init__(self, msg, position)

class EmptyTagError(NestingError):
    """Exception raised when empty elements have an end tag."""

    def __init__(self, tag, position=(None, None)):
        self.tag = tag
        msg = 'Close tag </%s> should be removed' % tag
        HTMLParseError.__init__(self, msg, position)

class HTMLTALParser(HTMLParser):

    # External API

    def __init__(self, gen=None):
        HTMLParser.__init__(self)
        if gen is None:
            gen = TALGenerator(xml=0)
        self.gen = gen
        self.tagstack = []
        self.nsstack = []
        self.nsdict = {'tal': ZOPE_TAL_NS, 'metal': ZOPE_METAL_NS}

    def parseFile(self, file):
        f = open(file)
        data = f.read()
        f.close()
        self.parseString(data)

    def parseString(self, data):
        self.feed(data)
        self.close()
        while self.tagstack:
            self.implied_endtag(self.tagstack[-1], 2)
        assert self.nsstack == [], self.nsstack

    def getCode(self):
        return self.gen.getCode()

    def getWarnings(self):
        return ()

    # Overriding HTMLParser methods

    def handle_starttag(self, tag, attrs):
        self.close_para_tags(tag)
        self.scan_xmlns(attrs)
        tag, attrlist, taldict, metaldict = self.process_ns(tag, attrs)
        self.tagstack.append(tag)
        self.gen.emitStartElement(tag, attrlist, taldict, metaldict,
                                  self.getpos())
        if tag in EMPTY_HTML_TAGS:
            self.implied_endtag(tag, -1)

    def handle_startendtag(self, tag, attrs):
        self.close_para_tags(tag)
        self.scan_xmlns(attrs)
        tag, attrlist, taldict, metaldict = self.process_ns(tag, attrs)
        if taldict.get("content"):
            self.gen.emitStartElement(tag, attrlist, taldict, metaldict,
                                      self.getpos())
            self.gen.emitEndElement(tag, implied=-1)
        else:
            self.gen.emitStartElement(tag, attrlist, taldict, metaldict,
                                      self.getpos(), isend=1)
        self.pop_xmlns()

    def handle_endtag(self, tag):
        if tag in EMPTY_HTML_TAGS:
            # </img> etc. in the source is an error
            raise EmptyTagError(tag, self.getpos())
        self.close_enclosed_tags(tag)
        self.gen.emitEndElement(tag)
        self.pop_xmlns()
        self.tagstack.pop()

    def close_para_tags(self, tag):
        if tag in EMPTY_HTML_TAGS:
            return
        close_to = -1
        if BLOCK_CLOSING_TAG_MAP.has_key(tag):
            blocks_to_close = BLOCK_CLOSING_TAG_MAP[tag]
            for i in range(len(self.tagstack)):
                t = self.tagstack[i]
                if t in blocks_to_close:
                    if close_to == -1:
                        close_to = i
                elif t in BLOCK_LEVEL_HTML_TAGS:
                    close_to = -1
        elif tag in PARA_LEVEL_HTML_TAGS + BLOCK_LEVEL_HTML_TAGS:
            for i in range(len(self.tagstack)):
                if self.tagstack[i] in BLOCK_LEVEL_HTML_TAGS:
                    close_to = -1
                elif self.tagstack[i] in PARA_LEVEL_HTML_TAGS:
                    if close_to == -1:
                        close_to = i
        if close_to >= 0:
            while len(self.tagstack) > close_to:
                self.implied_endtag(self.tagstack[-1], 1)

    def close_enclosed_tags(self, tag):
        if tag not in self.tagstack:
            raise NestingError(self.tagstack, tag, self.getpos())
        while tag != self.tagstack[-1]:
            self.implied_endtag(self.tagstack[-1], 1)
        assert self.tagstack[-1] == tag

    def implied_endtag(self, tag, implied):
        assert tag == self.tagstack[-1]
        assert implied in (-1, 1, 2)
        isend = (implied < 0)
        if tag in TIGHTEN_IMPLICIT_CLOSE_TAGS:
            # Pick out trailing whitespace from the program, and
            # insert the close tag before the whitespace.
            white = self.gen.unEmitWhitespace()
        else:
            white = None
        self.gen.emitEndElement(tag, isend=isend, implied=implied)
        if white:
            self.gen.emitRawText(white)
        self.tagstack.pop()
        self.pop_xmlns()

    def handle_charref(self, name):
        self.gen.emitRawText("&#%s;" % name)

    def handle_entityref(self, name):
        self.gen.emitRawText("&%s;" % name)

    def handle_data(self, data):
        self.gen.emitRawText(data)

    def handle_comment(self, data):
        self.gen.emitRawText("<!--%s-->" % data)

    def handle_decl(self, data):
        self.gen.emitRawText("<!%s>" % data)

    def handle_pi(self, data):
        self.gen.emitRawText("<?%s>" % data)

    # Internal thingies

    def scan_xmlns(self, attrs):
        nsnew = {}
        for key, value in attrs:
            if key[:6] == "xmlns:":
                nsnew[key[6:]] = value
        if nsnew:
            self.nsstack.append(self.nsdict)
            self.nsdict = self.nsdict.copy()
            self.nsdict.update(nsnew)
        else:
            self.nsstack.append(self.nsdict)

    def pop_xmlns(self):
        self.nsdict = self.nsstack.pop()

    def fixname(self, name):
        if ':' in name:
            prefix, suffix = string.split(name, ':', 1)
            if prefix == 'xmlns':
                nsuri = self.nsdict.get(suffix)
                if nsuri in (ZOPE_TAL_NS, ZOPE_METAL_NS):
                    return name, name, prefix
            else:
                nsuri = self.nsdict.get(prefix)
                if nsuri == ZOPE_TAL_NS:
                    return name, suffix, 'tal'
                elif nsuri == ZOPE_METAL_NS:
                    return name, suffix,  'metal'
        return name, name, 0

    def process_ns(self, name, attrs):
        attrlist = []
        taldict = {}
        metaldict = {}
        name, namebase, namens = self.fixname(name)
        for item in attrs:
            key, value = item
            key, keybase, keyns = self.fixname(key)
            ns = keyns or namens # default to tag namespace
            if ns and ns != 'unknown':
                item = (key, value, ns)
            if ns == 'tal':
                if taldict.has_key(keybase):
                    raise TALError("duplicate TAL attribute " +
                                   `keybase`, self.getpos())
                taldict[keybase] = value
            elif ns == 'metal':
                if metaldict.has_key(keybase):
                    raise METALError("duplicate METAL attribute " +
                                     `keybase`, self.getpos())
                metaldict[keybase] = value
            attrlist.append(item)
        if namens in ('metal', 'tal'):
            taldict['tal tag'] = namens
        return name, attrlist, taldict, metaldict
