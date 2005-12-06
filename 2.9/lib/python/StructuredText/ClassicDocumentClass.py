##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import re, ST, STDOM
from STletters import letters

from types import StringType, UnicodeType, ListType
StringTypes = (StringType, UnicodeType)

class StructuredTextExample(ST.StructuredTextParagraph):
    """Represents a section of document with literal text, as for examples"""

    def __init__(self, subs, **kw):
        t=[]; a=t.append
        for s in subs: a(s.getNodeValue())
        ST.StructuredTextParagraph.__init__(self, '\n\n'.join(t), (), **kw)

    def getColorizableTexts(self): return ()
    def setColorizableTexts(self, src): pass # never color examples

class StructuredTextBullet(ST.StructuredTextParagraph):
    """Represents a section of a document with a title and a body"""

class StructuredTextNumbered(ST.StructuredTextParagraph):
    """Represents a section of a document with a title and a body"""

class StructuredTextDescriptionTitle(ST.StructuredTextParagraph):
    """Represents a section of a document with a title and a body"""

class StructuredTextDescriptionBody(ST.StructuredTextParagraph):
    """Represents a section of a document with a title and a body"""

class StructuredTextDescription(ST.StructuredTextParagraph):
    """Represents a section of a document with a title and a body"""

    def __init__(self, title, src, subs, **kw):
        ST.StructuredTextParagraph.__init__(self, src, subs, **kw)
        self._title=title

    def getColorizableTexts(self): return self._title, self._src
    def setColorizableTexts(self, src): self._title, self._src = src

    def getChildren(self):
        return (StructuredTextDescriptionTitle(self._title),
                StructuredTextDescriptionBody(self._src, self._subs))

class StructuredTextSectionTitle(ST.StructuredTextParagraph):
    """Represents a section of a document with a title and a body"""

class StructuredTextSection(ST.StructuredTextParagraph):
    """Represents a section of a document with a title and a body"""
    def __init__(self, src, subs=None, **kw):
        ST.StructuredTextParagraph.__init__(
            self, StructuredTextSectionTitle(src), subs, **kw)

    def getColorizableTexts(self):
        return self._src.getColorizableTexts()

    def setColorizableTexts(self,src):
        self._src.setColorizableTexts(src)

# a StructuredTextTable holds StructuredTextRows
class StructuredTextTable(ST.StructuredTextDocument):
    """
    rows is a list of lists containing tuples, which
    represent the columns/cells in each rows.
    EX
    rows = [[('row 1:column1',1)],[('row2:column1',1)]]
    """

    def __init__(self, rows, src, subs, **kw):
        ST.StructuredTextDocument.__init__(self, subs, **kw)
        self._rows = []
        for row in rows:
            if row:
                self._rows.append(StructuredTextRow(row,kw))

    def getRows(self):
        return [self._rows]

    def _getRows(self):
        return self.getRows()

    def getColorizableTexts(self):
        """
        return a tuple where each item is a column/cell's
        contents. The tuple, result, will be of this format.
        ("r1 col1", "r1=col2", "r2 col1", "r2 col2")
        """

        #result = ()
        result = []
        for row in self._rows:
            for column in row.getColumns()[0]:
                #result = result[:] + (column.getColorizableTexts(),)
                result.append(column.getColorizableTexts()[0])
        return result

    def setColorizableTexts(self,texts):
        """
        texts is going to a tuple where each item is the
        result of being mapped to the colortext function.
        Need to insert the results appropriately into the
        individual columns/cells
        """
        for row_index in range(len(self._rows)):
            for column_index in range(len(self._rows[row_index]._columns)):
                self._rows[row_index]._columns[column_index].setColorizableTexts((texts[0],))
                texts = texts[1:]

    def _getColorizableTexts(self):
        return self.getColorizableTexts()

    def _setColorizableTexts(self):
        return self.setColorizableTexts()

# StructuredTextRow holds StructuredTextColumns
class StructuredTextRow(ST.StructuredTextDocument):

    def __init__(self,row,kw):
        """
        row is a list of tuples, where each tuple is
        the raw text for a cell/column and the span
        of that cell/column.
        EX
        [('this is column one',1), ('this is column two',1)]
        """
        ST.StructuredTextDocument.__init__(self, [], **kw)
        self._columns = []
        for column in row:
            self._columns.append(StructuredTextColumn(column[0],column[1],kw))
    def getColumns(self):
        return [self._columns]

    def _getColumns(self):
        return [self._columns]

# this holds the raw text of a table cell
class StructuredTextColumn(ST.StructuredTextParagraph):
    """
    StructuredTextColumn is a cell/column in a table.
    This contains the actual text of a column and is
    thus a StructuredTextParagraph. A StructuredTextColumn
    also holds the span of its column
    """

    def __init__(self,text,span,kw):
        ST.StructuredTextParagraph.__init__(self, text, [], **kw)
        self._span = span

    def getSpan(self):
        return self._span

    def _getSpan(self):
        return self._span

class StructuredTextMarkup(STDOM.Element):

    def __init__(self, v, **kw):
        self._value=v
        self._attributes=kw.keys()
        for k, v in kw.items(): setattr(self, k, v)

    def getChildren(self, type=type, lt=type([])):
        v=self._value
        if type(v) is not lt: v=[v]
        return v

    def getColorizableTexts(self): return self._value,
    def setColorizableTexts(self, v): self._value=v[0]

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, `self._value`)

class StructuredTextLiteral(StructuredTextMarkup):
    def getColorizableTexts(self): return ()
    def setColorizableTexts(self, v): pass

class StructuredTextEmphasis(StructuredTextMarkup): pass

class StructuredTextStrong(StructuredTextMarkup): pass

class StructuredTextInnerLink(StructuredTextMarkup): pass

class StructuredTextNamedLink(StructuredTextMarkup): pass

class StructuredTextUnderline(StructuredTextMarkup): pass

class StructuredTextLink(StructuredTextMarkup):
    "A simple hyperlink"

class DocumentClass:
    """
    Class instance calls [ex.=> x()] require a structured text
    structure. Doc will then parse each paragraph in the structure
    and will find the special structures within each paragraph.
    Each special structure will be stored as an instance. Special
    structures within another special structure are stored within
    the 'top' structure
    EX : '-underline this-' => would be turned into an underline
    instance. '-underline **this**' would be stored as an underline
    instance with a strong instance stored in its string
    """

    paragraph_types  = [
        'doc_bullet',
        'doc_numbered',
        'doc_description',
        'doc_header',
        'doc_table',
        ]

    text_types = [
        'doc_href1',
        'doc_href2',
        'doc_strong',
        'doc_emphasize',
        'doc_literal',
        'doc_inner_link',
        'doc_named_link',
        'doc_underline',
        ]

    def __call__(self, doc):
        if type(doc) in StringTypes:
            doc=ST.StructuredText(doc)
            doc.setSubparagraphs(self.color_paragraphs(
               doc.getSubparagraphs()))
        else:
            doc=ST.StructuredTextDocument(self.color_paragraphs(
               doc.getSubparagraphs()))
        return doc

    def parse(self, raw_string, text_type,
              type=type, sts=StringTypes, lt=type([])):

        """
        Parse accepts a raw_string, an expr to test the raw_string,
        and the raw_string's subparagraphs.

        Parse will continue to search through raw_string until
        all instances of expr in raw_string are found.

        If no instances of expr are found, raw_string is returned.
        Otherwise a list of substrings and instances is returned
        """

        tmp = []    # the list to be returned if raw_string is split
        append=tmp.append

        if type(text_type) in sts: text_type=getattr(self, text_type)

        while 1:
            t = text_type(raw_string)
            if not t: break
            #an instance of expr was found
            t, start, end    = t

            if start: append(raw_string[0:start])

            tt=type(t)
            if tt in sts:
                # if we get a string back, add it to text to be parsed
                raw_string = t+raw_string[end:len(raw_string)]
            else:
                if tt is lt:
                # is we get a list, append it's elements
                    tmp[len(tmp):]=t
                else:
                    # normal case, an object
                    append(t)
                raw_string = raw_string[end:len(raw_string)]

        if not tmp: return raw_string # nothing found

        if raw_string: append(raw_string)
        elif len(tmp)==1: return tmp[0]

        return tmp


    def color_text(self, str, types=None):
        """Search the paragraph for each special structure
        """
        if types is None: types=self.text_types

        for text_type in types:

            if type(str) in StringTypes:
                str = self.parse(str, text_type)
            elif type(str) is ListType:
                r=[]; a=r.append
                for s in str:
                    if type(s) in StringTypes:
                        s=self.parse(s, text_type)
                        if type(s) is ListType: r[len(r):]=s
                        else: a(s)
                    else:
                        s.setColorizableTexts(
                           map(self.color_text,
                               s.getColorizableTexts()
                               ))
                        a(s)
                str=r
            else:
                r=[]; a=r.append; color=self.color_text
                for s in str.getColorizableTexts():
                    color(s, (text_type,))
                    a(s)

                str.setColorizableTexts(r)

        return str

    def color_paragraphs(self, raw_paragraphs,
                           type=type, sequence_types=(type([]), type(())),
                           sts=StringTypes):
        result=[]
        for paragraph in raw_paragraphs:

            if paragraph.getNodeName() != 'StructuredTextParagraph':
                result.append(paragraph)
                continue

            for pt in self.paragraph_types:
                if type(pt) in sts:
                    # grab the corresponding function
                    pt=getattr(self, pt)
                # evaluate the paragraph
                r=pt(paragraph)
                if r:
                    if type(r) not in sequence_types:
                        r=r,
                    new_paragraphs=r
                    for paragraph in new_paragraphs:
                        paragraph.setSubparagraphs(self.color_paragraphs(paragraph.getSubparagraphs()))
                    break
            else:
                new_paragraphs=ST.StructuredTextParagraph(paragraph.getColorizableTexts()[0],
                                                             self.color_paragraphs(paragraph.getSubparagraphs()),
                                                             indent=paragraph.indent),
            # color the inline StructuredText types
            # for each StructuredTextParagraph
            for paragraph in new_paragraphs:
                paragraph.setColorizableTexts(
                   map(self.color_text,
                       paragraph.getColorizableTexts()
                       ))
                result.append(paragraph)

        return result

    def doc_table(self,paragraph, expr = re.compile('(\s*)([||]+)').match):
        #print "paragraph=>", type(paragraph), paragraph, paragraph._src
        text    = paragraph.getColorizableTexts()[0]
        m       = expr(text)

        if not (m):
            return None
        rows = []

        # initial split
        for row in text.split("\n"):
            rows.append(row)

        # clean up the rows
        for index in range(len(rows)):
            tmp = []
            rows[index] = rows[index].strip()
            l = len(rows[index])-2
            result = rows[index][:l].split("||")
            for text in result:
                if text:
                    tmp.append(text)
                    tmp.append('')
                else:
                    tmp.append(text)
            rows[index] = tmp
        # remove trailing '''s
        for index in range(len(rows)):
            l = len(rows[index])-1
            rows[index] = rows[index][:l]

        result = []
        for row in rows:
            cspan   = 0
            tmp     = []
            for item in row:
                if item:
                    tmp.append((item,cspan))
                    cspan = 0
                else:
                    cspan = cspan + 1
            result.append(tmp)

        subs = paragraph.getSubparagraphs()
#        indent=paragraph.indent
        return StructuredTextTable(result,text,subs,indent=paragraph.indent)

    def doc_bullet(self, paragraph, expr = re.compile('\s*[-*o]\s+').match):
        top=paragraph.getColorizableTexts()[0]
        m=expr(top)

        if not m:
            return None

        subs=paragraph.getSubparagraphs()
        if top[-2:]=='::':
            subs=[StructuredTextExample(subs)]
            top=top[:-1]
        return StructuredTextBullet(top[m.span()[1]:], subs,
                                     indent=paragraph.indent,
                                     bullet=top[:m.span()[1]]
                                     )

    def doc_numbered(
        self, paragraph,
        expr = re.compile('(\s*[%s]+\.)|(\s*[0-9]+\.)|(\s*[0-9]+\s+)' % letters).match):

        # This is the old expression. It had a nasty habit
        # of grabbing paragraphs that began with a single
        # letter word even if there was no following period.

        #expr = re.compile('\s*'
        #                   '(([a-zA-Z]|[0-9]+|[ivxlcdmIVXLCDM]+)\.)*'
        #                   '([a-zA-Z]|[0-9]+|[ivxlcdmIVXLCDM]+)\.?'
        #                   '\s+').match):

        top=paragraph.getColorizableTexts()[0]
        m=expr(top)
        if not m: return None
        subs=paragraph.getSubparagraphs()
        if top[-2:]=='::':
            subs=[StructuredTextExample(subs)]
            top=top[:-1]
        return StructuredTextNumbered(top[m.span()[1]:], subs,
                                        indent=paragraph.indent,
                                        number=top[:m.span()[1]])

    def doc_description(
        self, paragraph,
        delim = re.compile('\s+--\s+').search,
        nb=re.compile(r'[^\000- ]').search,
        ):

        top=paragraph.getColorizableTexts()[0]
        d=delim(top)
        if not d: return None
        start, end = d.span()
        title=top[:start]
        if title.find('\n') >= 0: return None
        if not nb(title): return None
        d=top[start:end]
        top=top[end:]

        subs=paragraph.getSubparagraphs()
        if top[-2:]=='::':
            subs=[StructuredTextExample(subs)]
            top=top[:-1]

        return StructuredTextDescription(
           title, top, subs,
           indent=paragraph.indent,
           delim=d)

    def doc_header(self, paragraph,
                    expr    = re.compile('[ %s0-9.:/,-_*<>\?\'\"]+' % letters).match
                    ):
        subs=paragraph.getSubparagraphs()
        if not subs: return None
        top=paragraph.getColorizableTexts()[0]
        if not top.strip(): return None
        if top[-2:]=='::':
            subs=StructuredTextExample(subs)
            if top.strip()=='::': return subs
            return ST.StructuredTextParagraph(top[:-1],
                                              [subs],
                                              indent=paragraph.indent,
                                              level=paragraph.level)

        if top.find('\n') >= 0: return None
        return StructuredTextSection(top, subs, indent=paragraph.indent, level=paragraph.level)

    def doc_literal(
        self, s,
        expr=re.compile(
          "(?:\s|^)'"                                               # open
          "([^ \t\n\r\f\v']|[^ \t\n\r\f\v'][^\n']*[^ \t\n\r\f\v'])" # contents
          "'(?:\s|[,.;:!?]|$)"                                      # close
          ).search):

        r=expr(s)
        if r:
            start, end = r.span(1)
            return (StructuredTextLiteral(s[start:end]), start-1, end+1)
        else:
            return None

    def doc_emphasize(
        self, s,
        expr = re.compile('\s*\*([ \n%s0-9.:/;,\'\"\?\=\-\>\<\(\)]+)\*(?!\*|-)' % letters).search
        ):

        r=expr(s)
        if r:
            start, end = r.span(1)
            return (StructuredTextEmphasis(s[start:end]), start-1, end+1)
        else:
            return None

    def doc_inner_link(self,
                       s,
                       expr1 = re.compile("\.\.\s*").search,
                       expr2 = re.compile("\[[%s0-9]+\]" % letters).search):

        # make sure we dont grab a named link
        if expr2(s) and expr1(s):
            start1,end1 = expr1(s).span()
            start2,end2 = expr2(s).span()
            if end1 == start2:
                # uh-oh, looks like a named link
                return None
            else:
                # the .. is somewhere else, ignore it
                return (StructuredTextInnerLink(s[start2+1,end2-1]),start2,end2)
            return None
        elif expr2(s) and not expr1(s):
            start,end = expr2(s).span()
            return (StructuredTextInnerLink(s[start+1:end-1]),start,end)
        return None

    def doc_named_link(self,
                       s,
                       expr=re.compile(r"(\.\.\s)(\[[%s0-9]+\])" % letters).search):

        result = expr(s)
        if result:
            start,end   = result.span(2)
            str = s[start+1:end-1]
            st,en       = result.span()
            return (StructuredTextNamedLink(str),st,en)
        return None

    def doc_underline(self,
                      s,
                      expr=re.compile("_([%s0-9\s\.,\?\/]+)_" % letters).search):


        result = expr(s)
        if result:
            start,end = result.span(1)
            st,e = result.span()
            return (StructuredTextUnderline(s[start:end]),st,e)
        else:
            return None

    def doc_strong(self,
                   s,
        expr = re.compile('\s*\*\*([ \n%s0-9.:/;\-,!\?\'\"]+)\*\*' % letters).search
        ):

        r=expr(s)
        if r:
            start, end = r.span(1)
            return (StructuredTextStrong(s[start:end]), start-2, end+2)
        else:
            return None



    def doc_href1(self, s,
        expr=re.compile("(\"[ %s0-9\n\-\.\,\;\(\)\/\:\/\*\']+\")(:)([a-zA-Z0-9\@\.\,\?\!\/\:\;\-\#\~]+)([,]*\s*)" % letters).search
        ):
        return self.doc_href(s, expr)

    def  doc_href2(self, s,
        expr=re.compile('(\"[ %s0-9\n\-\.\:\;\(\)\/\*\']+\")([,]+\s+)([a-zA-Z0-9\@\.\,\?\!\/\:\;\-\#\~]+)(\s*)' % letters).search
        ):
        return self.doc_href(s, expr)

    def doc_href(self, s, expr, punctuation = re.compile("[\,\.\?\!\;]+").match):

        r=expr(s)

        if r:
            # need to grab the href part and the
            # beginning part

            start,e = r.span(1)
            name    = s[start:e]
            name    = name.replace('"','',2)
            #start   = start + 1
            st,end   = r.span(3)
            if punctuation(s[end-1:end]):
                end = end -1
            link    = s[st:end]
            #end     = end - 1

            # name is the href title, link is the target
            # of the href
            return (StructuredTextLink(name, href=link),
                    start, end)

            #return (StructuredTextLink(s[start:end], href=s[start:end]),
            #        start, end)
        else:
            return None
