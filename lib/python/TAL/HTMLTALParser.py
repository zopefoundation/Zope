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

from TALGenerator import TALGenerator

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
        assert self.tagstack == []
        assert self.nsstack == []
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
        print tag, self.nsdict
        if tag not in EMPTY_HTML_TAGS:
            self.tagstack.append(tag)
        else:
            self.pop_xmlns()
            print "<", tag, self.nsdict
        self.gen.emitStartTag(tag, attrs)

    def finish_endtag(self, tag):
        if tag not in EMPTY_HTML_TAGS:
            if not tag:
                tag = self.tagstack.pop()
            else:
                assert tag in self.tagstack
                while self.tagstack[-1] != tag:
                    self.finish_endtag(None)
                self.tagstack.pop()
            self.pop_xmlns()
            print "<", tag, self.nsdict
        self.gen.emitEndTag(tag)

    def handle_charref(self, name):
        self.gen.emit("rawtext", "&#%s;" % name)

    def handle_entityref(self, name):
        self.gen.emit("rawtext", "&%s;" % name)

    def handle_data(self, data):
        self.gen.emit("text", data)

    def handle_comment(self, data):
        self.gen.emit("rawtext", "<!--%s-->" % data)

    def handle_pi(self, data):
        self.gen.emit("rawtext", "<?%s>" % data)
