import string

from TALGenerator import TALGenerator
from nsgmllib import SGMLParser

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

CLOSING_BLOCK_LEVEL_HTML_TAGS = [
    # These are HTML tags that close others in this list, but are not
    # closed by paragraph-level tags.  They don't close across other
    # block-level boundaries.
    "li", "dt", "dd", "td", "th", "tr",
    ]

BLOCK_LEVEL_HTML_TAGS = [
    # List of HTML tags that denote larger sections than paragraphs.
    "blockquote", "table", "tr", "th", "td", "thead", "tfoot", "tbody",
    "noframe", "ul", "ol", "li", "dl", "dt", "dd", "div",
    ]

TIGHTEN_IMPLICIT_CLOSE_TAGS = (PARA_LEVEL_HTML_TAGS
                               + CLOSING_BLOCK_LEVEL_HTML_TAGS)


class HTMLTALParser(SGMLParser):

    # External API

    def __init__(self, gen=None):
        SGMLParser.__init__(self)
        if gen is None:
            gen = TALGenerator()
        self.gen = gen
        self.tagstack = []
        self.nsstack = []
        self.nsdict = {}

    def parseFile(self, file):
        f = open(file)
        data = f.read()
        f.close()
        self.feed(data)
        self.close()
        while self.tagstack:
            self.finish_endtag(None)
        assert self.tagstack == [], self.tagstack
        assert self.nsstack == [], self.nsstack
        assert self.nsdict == {}, self.nsdict

    def getCode(self):
        return self.gen.program, self.gen.macros

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

    # Overriding SGMLParser methods

    def finish_starttag(self, tag, attrs):
        self.scan_xmlns(attrs)
        if tag in EMPTY_HTML_TAGS:
            self.pop_xmlns()
        elif tag in CLOSING_BLOCK_LEVEL_HTML_TAGS:
            close_to = -1
            for i in range(len(self.tagstack)):
                t = self.tagstack[i]
                if t in CLOSING_BLOCK_LEVEL_HTML_TAGS:
                    close_to = i
                elif t in BLOCK_LEVEL_HTML_TAGS:
                    close_to = -1
            self._close_to_level(close_to)
            self.tagstack.append(tag)
        elif tag in PARA_LEVEL_HTML_TAGS + BLOCK_LEVEL_HTML_TAGS:
            close_to = -1
            for i in range(len(self.tagstack)):
                if self.tagstack[i] in BLOCK_LEVEL_HTML_TAGS:
                    close_to = -1
                elif self.tagstack[i] in PARA_LEVEL_HTML_TAGS:
                    if close_to == -1:
                        close_to = i
            self._close_to_level(close_to)
            self.tagstack.append(tag)
        else:
            self.tagstack.append(tag)
        self.gen.emitStartTag(tag, attrs)

    def _close_to_level(self, close_to):
        if close_to > -1:
            closing = self.tagstack[close_to:]
            closing.reverse()
            for t in closing:
                self.finish_endtag(t, implied=1)

    def finish_endtag(self, tag, implied=0):
        if tag in EMPTY_HTML_TAGS:
            return
        assert tag in self.tagstack
        while self.tagstack[-1] != tag:
            self.finish_endtag(self.tagstack[-1], implied=1)
        self.tagstack.pop()
        self.pop_xmlns()
        if implied \
           and tag in TIGHTEN_IMPLICIT_CLOSE_TAGS \
           and self.gen.program \
           and self.gen.program[-1][0] == "rawtext":
            # Pick out trailing whitespace from the last instruction,
            # if it was a "rawtext" instruction, and insert the close
            # tag before the whitespace.
            data = self.gen.program.pop()[1]
            prefix = string.rstrip(data)
            white = data[len(prefix):]
            if data:
                self.gen.emitRawText(prefix)
            self.gen.emitEndTag(tag)
            if white:
                self.gen.emitRawText(white)
        else:
            self.gen.emitEndTag(tag)

    def handle_charref(self, name):
        self.gen.emitRawText("&#%s;" % name)

    def handle_entityref(self, name):
        self.gen.emitRawText("&%s;" % name)

    def handle_data(self, data):
        self.gen.emitText(data)

    def handle_comment(self, data):
        self.gen.emitRawText("<!--%s-->" % data)

    def handle_pi(self, data):
        self.gen.emitRawText("<?%s>" % data)
