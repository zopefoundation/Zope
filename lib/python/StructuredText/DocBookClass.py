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


class DocBookClass:

    element_types={
       '#text': '_text',
       'StructuredTextDocument': 'document',
       'StructuredTextParagraph': 'paragraph',
       'StructuredTextExample': 'example',
       'StructuredTextBullet': 'bullet',
       'StructuredTextNumbered': 'numbered',
       'StructuredTextDescription': 'description',
       'StructuredTextDescriptionTitle': 'descriptionTitle',
       'StructuredTextDescriptionBody': 'descriptionBody',
       'StructuredTextSection': 'section',
       'StructuredTextSectionTitle': 'sectionTitle',
       'StructuredTextLiteral': 'literal',
       'StructuredTextEmphasis': 'emphasis',
       'StructuredTextStrong': 'strong',
       'StructuredTextLink': 'link',
       'StructuredTextXref': 'xref',
       'StructuredTextSGML': 'sgml',
       }

    def dispatch(self, doc, level, output):
        getattr(self, self.element_types[doc.getNodeName()])(doc, level, output)

    def __call__(self, doc, level=1):
        r=[]
        self.dispatch(doc, level-1, r.append)
        return ''.join(r)

    def _text(self, doc, level, output):
        if doc.getNodeName() == 'StructuredTextLiteral':
            output(doc.getNodeValue())
        else:
            output(doc.getNodeValue().lstrip())

    def document(self, doc, level, output):
        output('<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook V4.1//EN">\n')
        output('<book>\n')
        children=doc.getChildNodes()
        if (children and
            children[0].getNodeName() == 'StructuredTextSection'):
            output('<title>%s</title>' % children[0].getChildNodes()[0].getNodeValue())
        for c in children:
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</book>\n')

    def section(self, doc, level, output):
        output('\n<section>\n')
        children=doc.getChildNodes()
        for c in children:
            getattr(self, self.element_types[c.getNodeName()])(c, level+1, output)
        output('\n</section>\n')

    def sectionTitle(self, doc, level, output):
        output('<title>')
        for c in doc.getChildNodes():
            try:
                getattr(self, self.element_types[c.getNodeName()])(c, level, output)
            except:
                print "failed", c.getNodeName(), c
        output('</title>\n')

    def description(self, doc, level, output):
        p=doc.getPreviousSibling()
        if p is None or  p.getNodeName() is not doc.getNodeName():
            output('<variablelist>\n')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        n=doc.getNextSibling()
        if n is None or n.getNodeName() is not doc.getNodeName():
            output('</variablelist>\n')

    def descriptionTitle(self, doc, level, output):
        output('<varlistentry><term>\n')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</term>\n')

    def descriptionBody(self, doc, level, output):
        output('<listitem><para>\n')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</para></listitem>\n')
        output('</varlistentry>\n')

    def bullet(self, doc, level, output):
        p=doc.getPreviousSibling()
        if p is None or p.getNodeName() is not doc.getNodeName():
            output('<itemizedlist>\n')
        output('<listitem><para>\n')

        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        n=doc.getNextSibling()
        output('</para></listitem>\n')
        if n is None or n.getNodeName() is not doc.getNodeName():
            output('</itemizedlist>\n')

    def numbered(self, doc, level, output):
        p=doc.getPreviousSibling()
        if p is None or p.getNodeName() is not doc.getNodeName():
            output('<orderedlist>\n')
        output('<listitem><para>\n')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        n=doc.getNextSibling()
        output('</para></listitem>\n')
        if n is None or n.getNodeName() is not doc.getNodeName():
            output('</orderedlist>\n')

    def example(self, doc, level, output):
        i=0
        for c in doc.getChildNodes():
            if i==0:
                output('<programlisting>\n<![CDATA[\n')
                ##
                ## eek.  A ']]>' in your body will break this...
                ##
                output(prestrip(c.getNodeValue()))
                output('\n]]></programlisting>\n')
            else:
                getattr(self, self.element_types[c.getNodeName()])(
                   c, level, output)

    def paragraph(self, doc, level, output):
        output('<para>\n\n')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(
               c, level, output)
        output('</para>\n\n')

    def link(self, doc, level, output):
        output('<ulink url="%s">' % doc.href)
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</ulink>')

    def emphasis(self, doc, level, output):
        output('<emphasis>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</emphasis> ')

    def literal(self, doc, level, output):
        output('<literal>')
        for c in doc.getChildNodes():
            output(c.getNodeValue())
        output('</literal>')

    def strong(self, doc, level, output):
        output('<emphasis>')
        for c in doc.getChildNodes():
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</emphasis>')

    def xref(self, doc, level, output):
        output('<xref linkend="%s"/>' % doc.getNodeValue())

    def sgml(self, doc, level, output):
        output(doc.getNodeValue())


def prestrip(v):
    v=v.replace( '\r\n', '\n')
    v=v.replace( '\r', '\n')
    v=v.replace( '\t', '        ')
    lines=v.split('\n')
    indent=len(lines[0])
    for line in lines:
        if not len(line): continue
        i=len(line)-len(line.lstrip())
        if i < indent:
            indent=i
    nlines=[]
    for line in lines:
        nlines.append(line[indent:])
    return '\n'.join(nlines, '\n')


class DocBookChapter(DocBookClass):

    def document(self, doc, level, output):
        output('<chapter>\n')
        children=doc.getChildNodes()
        if (children and
            children[0].getNodeName() == 'StructuredTextSection'):
            output('<title>%s</title>' % children[0].getChildNodes()[0].getNodeValue())
        for c in children[0].getChildNodes()[1:]:
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</chapter>\n')

ets = DocBookClass.element_types
ets.update({'StructuredTextImage': 'image'})

class DocBookChapterWithFigures(DocBookChapter):

    element_types = ets

    def image(self, doc, level, output):
        if hasattr(doc, 'key'):
            output('<figure id="%s"><title>%s</title>\n' % (doc.key, doc.getNodeValue()) )
        else:
            output('<figure><title>%s</title>\n' % doc.getNodeValue())
##        for c in doc.getChildNodes():
##            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('<graphic fileref="%s"></graphic>\n</figure>\n' % doc.href)

class DocBookArticle(DocBookClass):

    def document(self, doc, level, output):
        output('<!DOCTYPE article PUBLIC "-//OASIS//DTD DocBook V4.1//EN">\n')
        output('<article>\n')
        children=doc.getChildNodes()
        if (children and
            children[0].getNodeName() == 'StructuredTextSection'):
            output('<articleinfo>\n<title>%s</title>\n</articleinfo>\n' %
                   children[0].getChildNodes()[0].getNodeValue())
        for c in children:
            getattr(self, self.element_types[c.getNodeName()])(c, level, output)
        output('</article>\n')


class DocBookBook:

    def __init__(self, title=''):
        self.title = title
        self.chapters = []

    def addChapter(self, chapter):
        self.chapters.append(chapter)

    def read(self):
        out = '<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook V4.1//EN">\n<book>\n'
        out = out + '<title>%s</title>\n' % self.title
        for chapter in self.chapters:
            out = out + chapter + '\n</book>\n'

        return out

    def __str__(self):
        return self.read()
