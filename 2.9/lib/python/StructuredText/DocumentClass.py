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
from STletters import letters, digits, literal_punc, under_punc,\
     strongem_punc, phrase_delimiters,dbl_quoted_punc

from types import StringType, UnicodeType, ListType
StringTypes = (StringType, UnicodeType)

def flatten(obj, append):
    if obj.getNodeType()==STDOM.TEXT_NODE:
        append(obj.getNodeValue())
    else:
        for child in obj.getChildNodes():
            flatten(child, append)


class StructuredTextExample(ST.StructuredTextParagraph):
    """Represents a section of document with literal text, as for examples"""

    def __init__(self, subs, **kw):
        t=[]
        a=t.append
        for s in subs:
            flatten(s, a)
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
class StructuredTextTable(ST.StructuredTextParagraph):
    """
    rows is a list of lists containing tuples, which
    represent the columns/cells in each rows.
    EX
    rows = [[('row 1:column1',1)],[('row2:column1',1)]]
    """

    def __init__(self, rows, src, subs, **kw):
        ST.StructuredTextParagraph.__init__(self, subs, **kw)
        self._rows = []
        for row in rows:
            if row:
                self._rows.append(StructuredTextRow(row,kw))

    def getRows(self):
        return [self._rows]

    def _getRows(self):
        return self.getRows()

    def getColumns(self):
        result = []
        for row in self._rows:
            result.append(row.getColumns())
        return result

    def _getColumns(self):
        return self.getColumns()

    def setColumns(self,columns):
        for index in range(len(self._rows)):
            self._rows[index].setColumns(columns[index])

    def _setColumns(self,columns):
        return self.setColumns(columns)

    def getColorizableTexts(self):
        """
        return a tuple where each item is a column/cell's
        contents. The tuple, result, will be of this format.
        ("r1 col1", "r1=col2", "r2 col1", "r2 col2")
        """

        result = []
        for row in self._rows:
            for column in row.getColumns()[0]:
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

    def _setColorizableTexts(self, texts):
        return self.setColorizableTexts(texts)

# StructuredTextRow holds StructuredTextColumns
class StructuredTextRow(ST.StructuredTextParagraph):

    def __init__(self,row,kw):
        """
        row is a list of tuples, where each tuple is
        the raw text for a cell/column and the span
        of that cell/column.
        EX
        [('this is column one',1), ('this is column two',1)]
        """

        ST.StructuredTextParagraph.__init__(self, [], **kw)

        self._columns = []
        for column in row:
            self._columns.append(StructuredTextColumn(column[0],
                                                      column[1],
                                                      column[2],
                                                      column[3],
                                                      column[4],
                                                      kw))

    def getColumns(self):
        return [self._columns]

    def _getColumns(self):
        return [self._columns]

    def setColumns(self,columns):
        self._columns = columns

    def _setColumns(self,columns):
        return self.setColumns(columns)

# this holds the text of a table cell
class StructuredTextColumn(ST.StructuredTextParagraph):
    """
    StructuredTextColumn is a cell/column in a table.
    A cell can hold multiple paragraphs. The cell
    is either classified as a StructuredTextTableHeader
    or StructuredTextTableData.
    """

    def __init__(self,text,span,align,valign,typ,kw):
        ST.StructuredTextParagraph.__init__(self, text, [], **kw)
        self._span = span
        self._align = align
        self._valign = valign
        self._type = typ

    def getSpan(self):
        return self._span

    def _getSpan(self):
        return self._span

    def getAlign(self):
        return self._align

    def _getAlign(self):
        return self.getAlign()

    def getValign(self):
        return self._valign

    def _getValign(self):
        return self.getValign()

    def getType(self):
        return self._type

    def _getType(self):
        return self.getType()

class StructuredTextTableHeader(ST.StructuredTextParagraph): pass

class StructuredTextTableData(ST.StructuredTextParagraph): pass

class StructuredTextMarkup(STDOM.Element):

    def __init__(self, v, **kw):
        self._value=v
        self._attributes=kw.keys()
        for k, v in kw.items(): setattr(self, k, v)

    def getChildren(self):
        v=self._value
        if not isinstance(v, ListType): v=[v]
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

class StructuredTextSGML(StructuredTextMarkup): pass

class StructuredTextLink(StructuredTextMarkup): pass

class StructuredTextXref(StructuredTextMarkup): pass

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

    #'doc_inner_link',
    #'doc_named_link',
    #'doc_underline'
    text_types = [
        'doc_literal',
        'doc_sgml',
        'doc_inner_link',
        'doc_named_link',
        'doc_href1',
        'doc_href2',
        'doc_strong',
        'doc_emphasize',
        'doc_underline',
        'doc_sgml',
        'doc_xref',
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
                        subs = self.color_paragraphs(paragraph.getSubparagraphs())
                        paragraph.setSubparagraphs(subs)
                    break
            else:
                # copy, retain attributes
                kw = {}
                atts = getattr(paragraph, '_attributes', [])
                for att in atts: kw[att] = getattr(paragraph, att)
                subs = self.color_paragraphs(paragraph.getSubparagraphs())
                new_paragraphs=ST.StructuredTextParagraph(
                   paragraph. getColorizableTexts()[0], subs, **kw),

            # color the inline StructuredText types
            # for each StructuredTextParagraph
            for paragraph in new_paragraphs:

                if paragraph.getNodeName() is "StructuredTextTable":
#                cells = paragraph.getColumns()
                    text = paragraph.getColorizableTexts()
                    text = map(ST.StructuredText,text)
                    text = map(self.__call__,text)
                    for t in range(len(text)):
                        text[t] = text[t].getSubparagraphs()
                    paragraph.setColorizableTexts(text)

                paragraph.setColorizableTexts(
                   map(self.color_text,
                       paragraph.getColorizableTexts()
                       ))
                result.append(paragraph)

        return result

    def doc_table(self, paragraph, expr = re.compile(r'\s*\|[-]+\|').match):
        text    = paragraph.getColorizableTexts()[0]
        m       = expr(text)

        subs = paragraph.getSubparagraphs()

        if not (m):
            return None
        rows = []

        spans   = []
        ROWS    = []
        COLS    = []
        indexes = []
        ignore  = []

        TDdivider   = re.compile("[\-]+").match
        THdivider   = re.compile("[\=]+").match
        col         = re.compile('\|').search
        innertable  = re.compile('\|([-]+|[=]+)\|').search

        text = text.strip()
        rows = text.split('\n')
        foo  = ""

        for row in range(len(rows)):
            rows[row] = rows[row].strip()

        # have indexes store if a row is a divider
        # or a cell part
        for index in range(len(rows)):
            tmpstr = rows[index][1:len(rows[index])-1]
            if TDdivider(tmpstr):
                indexes.append("TDdivider")
            elif THdivider(tmpstr):
                indexes.append("THdivider")
            else:
                indexes.append("cell")

        for index in range(len(indexes)):
            if indexes[index] is "TDdivider" or indexes[index] is "THdivider":
                ignore = [] # reset ignore
                #continue    # skip dividers

            tmp     = rows[index].strip()    # clean the row up
            tmp     = tmp[1:len(tmp)-1]     # remove leading + trailing |
            offset  = 0

            # find the start and end of inner
            # tables. ignore everything between
            if innertable(tmp):
                tmpstr = tmp.strip()
                while innertable(tmpstr):
                    start,end   = innertable(tmpstr).span()
                    if not (start,end-1) in ignore:
                        ignore.append((start,end-1))
                    tmpstr = " " + tmpstr[end:]

            # find the location of column dividers
            # NOTE: |'s in inner tables do not count
            #   as column dividers
            if col(tmp):
                while col(tmp):
                    bar         = 1   # true if start is not in ignore
                    start,end   = col(tmp).span()

                    if not start+offset in spans:
                        for s,e in ignore:
                            if start+offset >= s or start+offset <= e:
                                bar = None
                                break
                        if bar:   # start is clean
                            spans.append(start+offset)
                    if not bar:
                        foo = foo + tmp[:end]
                        tmp = tmp[end:]
                        offset = offset + end
                    else:
                        COLS.append((foo + tmp[0:start],start+offset))
                        foo = ""
                        tmp = " " + tmp[end:]
                        offset = offset + start
            if not offset+len(tmp) in spans:
                spans.append(offset+len(tmp))
            COLS.append((foo + tmp,offset+len(tmp)))
            foo = ""
            ROWS.append(COLS)
            COLS = []

        spans.sort()
        ROWS = ROWS[1:len(ROWS)]

        # find each column span
        cols    = []
        tmp     = []

        for row in ROWS:
            for c in row:
                tmp.append(c[1])
            cols.append(tmp)
            tmp = []

        cur = 1
        tmp = []
        C   = []
        for col in cols:
            for span in spans:
                if not span in col:
                    cur = cur + 1
                else:
                    tmp.append(cur)
                    cur = 1
            C.append(tmp)
            tmp = []

        for index in range(len(C)):
            for i in range(len(C[index])):
                ROWS[index][i] = (ROWS[index][i][0],C[index][i])
        rows = ROWS

        # label things as either TableData or
        # Table header
        TD  = []
        TH  = []
        all = []
        for index in range(len(indexes)):
            if indexes[index] is "TDdivider":
                TD.append(index)
                all.append(index)
            if indexes[index] is "THdivider":
                TH.append(index)
                all.append(index)
        TD = TD[1:]
        dividers = all[1:]
        #print "TD  => ", TD
        #print "TH  => ", TH
        #print "all => ", all, "\n"

        for div in dividers:
            if div in TD:
                index = all.index(div)
                for rowindex in range(all[index-1],all[index]):
                    for i in range(len(rows[rowindex])):
                        rows[rowindex][i] = (rows[rowindex][i][0],
                                             rows[rowindex][i][1],
                                             "td")
            else:
                index = all.index(div)
                for rowindex in range(all[index-1],all[index]):
                    for i in range(len(rows[rowindex])):
                        rows[rowindex][i] = (rows[rowindex][i][0],
                                             rows[rowindex][i][1],
                                             "th")

        # now munge the multi-line cells together
        # as paragraphs
        ROWS    = []
        COLS    = []
        for row in rows:
            for index in range(len(row)):
                if not COLS:
                    COLS = range(len(row))
                    for i in range(len(COLS)):
                        COLS[i] = ["",1,""]
                if TDdivider(row[index][0]) or THdivider(row[index][0]):
                    ROWS.append(COLS)
                    COLS = []
                else:
                    COLS[index][0] = COLS[index][0] + (row[index][0]) + "\n"
                    COLS[index][1] = row[index][1]
                    COLS[index][2] = row[index][2]

        # now that each cell has been munged together,
        # determine the cell's alignment.
        # Default is to center. Also determine the cell's
        # vertical alignment, top, middle, bottom. Default is
        # to middle
        rows = []
        cols = []
        for row in ROWS:
            for index in range(len(row)):
                topindent       = 0
                bottomindent    = 0
                leftindent      = 0
                rightindent     = 0
                left            = []
                right           = []
                text            = row[index][0]
                text            = text.split('\n')
                text            = text[:len(text)-1]
                align           = ""
                valign          = ""
                for t in text:
                    t = t.strip()
                    if not t:
                        topindent = topindent + 1
                    else:
                        break
                text.reverse()
                for t in text:
                    t = t.strip()
                    if not t:
                        bottomindent = bottomindent + 1
                    else:
                        break
                text.reverse()
                tmp   = '\n'.join(text[topindent:len(text)-bottomindent])
                pars  = re.compile("\n\s*\n").split(tmp)
                for par in pars:
                    if index > 0:
                        par = par[1:]
                    par = par.split(' ')
                    for p in par:
                        if not p:
                            leftindent = leftindent+1
                        else:
                            break
                    left.append(leftindent)
                    leftindent = 0
                    par.reverse()
                    for p in par:
                        if not p:
                            rightindent = rightindent + 1
                        else:
                            break
                    right.append(rightindent)
                    rightindent = 0
                left.sort()
                right.sort()

                if topindent == bottomindent:
                    valign="middle"
                elif topindent < 1:
                    valign="top"
                elif bottomindent < 1:
                    valign="bottom"
                else:
                    valign="middle"

                if left[0] < 1:
                    align = "left"
                elif right[0] < 1:
                    align = "right"
                elif left[0] > 1 and right[0] > 1:
                    align="center"
                else:
                    align="left"

                cols.append((row[index][0],row[index][1],align,valign,row[index][2]))
            rows.append(cols)
            cols = []
        return StructuredTextTable(rows,text,subs,indent=paragraph.indent)

    def doc_bullet(self, paragraph, expr = re.compile(r'\s*[-*o]\s+').match):
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
        expr = re.compile(r'(\s*[%s]\.)|(\s*[0-9]+\.)|(\s*[0-9]+\s+)' % letters).match):

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
        delim = re.compile(r'\s+--\s+').search,
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

    def doc_header(self, paragraph):
        subs=paragraph.getSubparagraphs()
        if not subs: return None
        top=paragraph.getColorizableTexts()[0]
        if not top.strip(): return None
        if top[-2:]=='::':
            subs=StructuredTextExample(subs)
            if top.strip()=='::': return subs
            # copy attrs when returning a paragraph
            kw = {}
            atts = getattr(paragraph, '_attributes', [])
            for att in atts: kw[att] = getattr(paragraph, att)
            return ST.StructuredTextParagraph(top[:-1], [subs], **kw)

        if top.find('\n') >= 0: return None
        return StructuredTextSection(top, subs, indent=paragraph.indent)

    def doc_literal(
        self, s,
        expr = re.compile(r"(\W+|^)'([%s%s%s\s]+)'([%s]+|$)" % (letters, digits, literal_punc, phrase_delimiters)).search,):

        # old expr... failed to cross newlines.
        #        expr=re.compile(
        #          r"(?:\s|^)'"           # open
        #          r"([^ \t\n\r\f\v']|[^ \t\n\r\f\v'][^\n\r']*[^ \t\n\r\f\v'])" # contents
        #          r"'(?:\s|[,.;:!?]|$)"  # close
        #          ).search):

        r=expr(s) #or expr2(s)
        if r:
            start, end = r.span(2)
            return (StructuredTextLiteral(s[start:end]), start-1, end+1)
        else:
            return None

    def doc_emphasize(
        self, s,
        expr = re.compile(r'\*([%s%s%s\s]+?)\*' % (letters, digits, strongem_punc)).search
        #expr = re.compile(r'\s*\*([ \n\r%s0-9.:/;,\'\"\?\-\_\/\=\-\>\<\(\)]+)\*(?!\*|-)' % letters).search       # old expr, inconsistent punctuation
        ):

        r=expr(s)
        if r:
            start, end = r.span(1)
            return (StructuredTextEmphasis(s[start:end]), start-1, end+1)
        else:
            return None

    def doc_inner_link(self,
                       s,
                       expr1 = re.compile(r"\.\.\s*").search,
                       expr2 = re.compile(r"\[[%s%s]+\]" % (letters, digits) ).search):

        # make sure we dont grab a named link
        if expr2(s) and expr1(s):
            start1,end1 = expr1(s).span()
            start2,end2 = expr2(s).span()
            if end1 == start2:
                # uh-oh, looks like a named link
                return None
            else:
                # the .. is somewhere else, ignore it
                return (StructuredTextInnerLink(s[start2+1:end2-1]),start2,end2)
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
                      expr=re.compile(r'_([%s%s%s\s]+)_([\s%s]|$)' % (letters, digits, under_punc,phrase_delimiters)).search):

        result = expr(s)
        if result:
            if result.group(1)[:1] == '_':
                return None # no double unders
            start,end = result.span(1)
            st,e = result.span()
            return (StructuredTextUnderline(s[start:end]),st,e-len(result.group(2)))
        else:
            return None

    def doc_strong(self,
                   s,
                   expr = re.compile(r'\*\*([%s%s%s\s]+?)\*\*' % (letters, digits, strongem_punc)).search
                   #expr = re.compile(r'\s*\*\*([ \n\r%s0-9.:/;,\'\"\?\-\_\/\=\-\>\<\(\)]+)\*\*(?!\*|-)' % letters).search, # old expr, inconsistent punc, failed to cross newlines.
        ):

        r=expr(s)
        if r:
            start, end = r.span(1)
            return (StructuredTextStrong(s[start:end]), start-2, end+2)
        else:
            return None

    ## Some constants to make the doc_href() regex easier to read.
    _DQUOTEDTEXT = r'("[ %s0-9\n\r%s]+")' % (letters,dbl_quoted_punc) ## double quoted text
    _ABSOLUTE_URL=r'((http|https|ftp|mailto|file|about)[:/]+?[%s0-9_\@\.\,\?\!\/\:\;\-\#\~\=\&\%%\+]+)' % letters
    _ABS_AND_RELATIVE_URL=r'([%s0-9_\@\.\,\?\!\/\:\;\-\#\~\=\&\%%\+]+)' % letters

    _SPACES = r'(\s*)'


    def doc_href1(self, s,
                  expr=re.compile(_DQUOTEDTEXT + "(:)" + _ABS_AND_RELATIVE_URL + _SPACES).search
                   ):
        return self.doc_href(s, expr)

    def doc_href2(self, s,
                  expr=re.compile(_DQUOTEDTEXT + r'(\,\s+)' + _ABSOLUTE_URL + _SPACES).search
                   ):
        return self.doc_href(s, expr)


    def doc_href(self, s, expr, punctuation=re.compile(r"[\,\.\?\!\;]+").match):

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

    def doc_sgml(self,s,expr=re.compile(r"\<[%s0-9\.\=\'\"\:\/\-\#\+\s\*]+\>" % letters).search):
        """
        SGML text is ignored and outputed as-is
        """
        r = expr(s)
        if r:
            start,end = r.span()
            text = s[start:end]
            return (StructuredTextSGML(text),start,end)
        else:
            return None


    def doc_xref(self, s,
        expr = re.compile('\[([%s0-9\-.:/;,\n\r\~]+)\]' % letters).search
        ):
        r = expr(s)
        if r:
            start, end = r.span(1)
            return (StructuredTextXref(s[start:end]), start-1, end+1)
        else:
            return None
