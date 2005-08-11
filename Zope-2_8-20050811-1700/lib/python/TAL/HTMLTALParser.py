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
Parse HTML and compile to TALInterpreter intermediate code.
"""

import sys

from TALGenerator import TALGenerator
from HTMLParser import HTMLParser, HTMLParseError
from TALDefs import \
     ZOPE_METAL_NS, ZOPE_TAL_NS, ZOPE_I18N_NS, METALError, TALError, I18NError

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
                       % ('>, <'.join(tagstack), endtag))
        else:
            msg = 'No tags are open to match </%s>' % endtag
        HTMLParseError.__init__(self, msg, position)

class EmptyTagError(NestingError):
    """Exception raised when empty elements have an end tag."""

    def __init__(self, tag, position=(None, None)):
        self.tag = tag
        msg = 'Close tag </%s> should be removed' % tag
        HTMLParseError.__init__(self, msg, position)

class OpenTagError(NestingError):
    """Exception raised when a tag is not allowed in another tag."""

    def __init__(self, tagstack, tag, position=(None, None)):
        self.tag = tag
        msg = 'Tag <%s> is not allowed in <%s>' % (tag, tagstack[-1])
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
        self.nsdict = {'tal': ZOPE_TAL_NS,
                       'metal': ZOPE_METAL_NS,
                       'i18n': ZOPE_I18N_NS,
                       }

    def parseFile(self, file):
        f = open(file)
        data = f.read()
        f.close()
        try:
            self.parseString(data)
        except TALError, e:
            e.setFile(file)
            raise

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
        tag, attrlist, taldict, metaldict, i18ndict \
             = self.process_ns(tag, attrs)
        if tag in EMPTY_HTML_TAGS and taldict.get("content"):
            raise TALError(
                "empty HTML tags cannot use tal:content: %s" % `tag`,
                self.getpos())
        self.tagstack.append(tag)
        self.gen.emitStartElement(tag, attrlist, taldict, metaldict, i18ndict,
                                  self.getpos())
        if tag in EMPTY_HTML_TAGS:
            self.implied_endtag(tag, -1)

    def handle_startendtag(self, tag, attrs):
        self.close_para_tags(tag)
        self.scan_xmlns(attrs)
        tag, attrlist, taldict, metaldict, i18ndict \
             = self.process_ns(tag, attrs)
        if taldict.get("content"):
            if tag in EMPTY_HTML_TAGS:
                raise TALError(
                    "empty HTML tags cannot use tal:content: %s" % `tag`,
                    self.getpos())
            self.gen.emitStartElement(tag, attrlist, taldict, metaldict,
                                      i18ndict, self.getpos())
            self.gen.emitEndElement(tag, implied=-1)
        else:
            self.gen.emitStartElement(tag, attrlist, taldict, metaldict,
                                      i18ndict, self.getpos(), isend=1)
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
            i = len(self.tagstack) - 1
            while i >= 0:
                closetag = self.tagstack[i]
                if closetag in BLOCK_LEVEL_HTML_TAGS:
                    break
                if closetag in PARA_LEVEL_HTML_TAGS:
                    if closetag != "p":
                        raise OpenTagError(self.tagstack, tag, self.getpos())
                    close_to = i
                i = i - 1
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
            if key.startswith("xmlns:"):
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
            prefix, suffix = name.split(':', 1)
            if prefix == 'xmlns':
                nsuri = self.nsdict.get(suffix)
                if nsuri in (ZOPE_TAL_NS, ZOPE_METAL_NS, ZOPE_I18N_NS):
                    return name, name, prefix
            else:
                nsuri = self.nsdict.get(prefix)
                if nsuri == ZOPE_TAL_NS:
                    return name, suffix, 'tal'
                elif nsuri == ZOPE_METAL_NS:
                    return name, suffix,  'metal'
                elif nsuri == ZOPE_I18N_NS:
                    return name, suffix, 'i18n'
        return name, name, 0

    def process_ns(self, name, attrs):
        attrlist = []
        taldict = {}
        metaldict = {}
        i18ndict = {}
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
            elif ns == 'i18n':
                if i18ndict.has_key(keybase):
                    raise I18NError("duplicate i18n attribute " +
                                    `keybase`, self.getpos())
                i18ndict[keybase] = value
            attrlist.append(item)
        if namens in ('metal', 'tal'):
            taldict['tal tag'] = namens
        return name, attrlist, taldict, metaldict, i18ndict
