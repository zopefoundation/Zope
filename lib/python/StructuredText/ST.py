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

import re, STDOM
from types import ListType

#####################################################################
#                              Updated functions                    #
#####################################################################

def indention(str,front = re.compile("^\s+").match):
    """
    Find the number of leading spaces. If none, return 0.
    """

    result = front(str)
    if result is not None:
        start, end = result.span()
        return end-start
    else:
        return 0     # no leading spaces

def insert(struct, top, level):
    """
    find what will be the parant paragraph of
    a sentence and return that paragraph's
    sub-paragraphs. The new paragraph will be
    appended to those sub-paragraphs
    """
    #print "struct", struct, top-1
    if not top-1 in range(len(struct)):
        if struct:
            return struct[len(struct)-1].getSubparagraphs()
        return struct
    run = struct[top-1]
    i    = 0
    while i+1 < level:
        run = run.getSubparagraphs()[len(run.getSubparagraphs())-1]
        i = i + 1
    #print "parent for level ", level, " was => ", run.getColorizableTexts()
    return run.getSubparagraphs()

def display(struct):
    """
    runs through the structure and prints out
    the paragraphs. If the insertion works
    correctly, display's results should mimic
    the orignal paragraphs.
    """

    if struct.getColorizableTexts():
        print join(struct.getColorizableTexts()),"\n"
    if struct.getSubparagraphs():
        for x in struct.getSubparagraphs():
            display(x)

def display2(struct):
    """
    runs through the structure and prints out
    the paragraphs. If the insertion works
    correctly, display's results should mimic
    the orignal paragraphs.
    """

    if struct.getNodeValue():
        print struct.getNodeValue(),"\n"
    if struct.getSubparagraphs():
        for x in struct.getSubparagraphs():
            display(x)

def findlevel(levels,indent):
    """
    remove all level information of levels
    with a greater level of indentation.
    Then return which level should insert this
    paragraph
    """

    keys = levels.keys()
    for key in keys:
        if levels[key] > indent:
            del(levels[key])
    keys = levels.keys()
    if not(keys):
        return 0
    else:
        for key in keys:
            if levels[key] == indent:
                return key
    highest = 0
    for key in keys:
        if key > highest:
            highest = key
    return highest-1

para_delim = r'(\n\s*\n|\r\n\s*\r\n)' # UNIX or DOS line endings, respectively

#####################################################################

# Golly, the capitalization of this function always makes me think it's a class
def StructuredText(paragraphs, delimiter=re.compile(para_delim)):
    """
    StructuredText accepts paragraphs, which is a list of
    lines to be parsed. StructuredText creates a structure
    which mimics the structure of the paragraphs.
    Structure => [paragraph,[sub-paragraphs]]
    """

    currentlevel    = 0
    currentindent  = 0
    levels            = {0:0}
    level             = 0        # which header are we under
    struct            = []      # the structure to be returned
    run                = struct

    paragraphs = paragraphs.expandtabs()
    paragraphs = '%s%s%s' % ('\n\n', paragraphs, '\n\n')
    paragraphs = delimiter.split(paragraphs)
    paragraphs = [ x for x in  paragraphs if x.strip() ]

    if not paragraphs: return StructuredTextDocument()

    ind = []     # structure based on indention levels
    for paragraph in paragraphs:
        ind.append([indention(paragraph), paragraph])

    currentindent = indention(paragraphs[0])
    levels[0]        = currentindent

    #############################################################
    #                                  updated                  #
    #############################################################

    for indent,paragraph in ind :
        if indent == 0:
            level          = level + 1
            currentlevel   = 0
            currentindent  = 0
            levels         = {0:0}
            struct.append(StructuredTextParagraph(paragraph, indent=indent, level=currentlevel))
        elif indent > currentindent:
            currentlevel            = currentlevel + 1
            currentindent           = indent
            levels[currentlevel]    = indent
            run = insert(struct,level,currentlevel)
            run.append(StructuredTextParagraph(paragraph, indent=indent, level=currentlevel))
        elif indent < currentindent:
            result   = findlevel(levels,indent)
            if result > 0:
                currentlevel = result
            currentindent  = indent
            if not level:
                struct.append(StructuredTextParagraph(paragraph, indent=indent, level=currentlevel))
            else:
                run = insert(struct,level,currentlevel)
                run.append(StructuredTextParagraph(paragraph, indent=indent, level=currentlevel))
        else:
            if insert(struct,level,currentlevel):
                run = insert(struct,level,currentlevel)
            else:
                run = struct
                currentindent = indent
            run.append(StructuredTextParagraph(paragraph, indent=indent, level=currentlevel))

    return StructuredTextDocument(struct)

Basic = StructuredText

class StructuredTextParagraph(STDOM.Element):

    indent=0

    def __init__(self, src, subs=None, **kw):
        if subs is None: subs=[]
        self._src=src
        self._subs=list(subs)

        self._attributes=kw.keys()
        for k, v in kw.items(): setattr(self, k, v)

    def getChildren(self):
        src=self._src
        if not isinstance(src, ListType): src=[src]
        return src+self._subs

    def getAttribute(self, name):
        return getattr(self, name, None)

    def getAttributeNode(self, name):
        if hasattr(self, name):
            return STDOM.Attr(name, getattr(self, name))
        else:
            return None

    def getAttributes(self):
        d={}
        for a in self._attributes:
            d[a]=getattr(self, a, '')
        return STDOM.NamedNodeMap(d)

    def getSubparagraphs(self):
        return self._subs

    def setSubparagraphs(self, subs):
        self._subs=subs

    def getColorizableTexts(self):
        return (self._src,)

    def setColorizableTexts(self, src):
        self._src=src[0]

    def __repr__(self):
        r=[]; a=r.append
        a((' '*(self.indent or 0))+
          ('%s(' % self.__class__.__name__)
          +str(self._src)+', ['
          )
        for p in self._subs: a(`p`)
        a((' '*(self.indent or 0))+'])')
        return '\n'.join(r)

    """
    create aliases for all above functions in the pythony way.
    """

    def _get_Children(self):
        return self.getChildren()

    def _get_Attribute(self, name):
        return self.getAttribute(name)

    def _get_AttributeNode(self, name):
        return self.getAttributeNode(name)

    def _get_Attributes(self):
        return self.getAttributes()

    def _get_Subparagraphs(self):
        return self.getSubparagraphs()

    def _set_Subparagraphs(self, subs):
        return self.setSubparagraphs(subs)

    def _get_ColorizableTexts(self):
        return self.getColorizableTexts()

    def _set_ColorizableTexts(self, src):
        return self.setColorizableTexts(src)

class StructuredTextDocument(StructuredTextParagraph):
    """
    A StructuredTextDocument holds StructuredTextParagraphs
    as its subparagraphs.
    """
    _attributes=()

    def __init__(self, subs=None, **kw):
        StructuredTextParagraph.__init__(self, '', subs, **kw)

    def getChildren(self):
        return self._subs

    def getColorizableTexts(self):
        return ()

    def setColorizableTexts(self, src):
        pass

    def __repr__(self):
        r=[]; a=r.append
        a('%s([' % self.__class__.__name__)
        for p in self._subs: a(`p`+',')
        a('])')
        return '\n'.join(r)

    """
    create aliases for all above functions in the pythony way.
    """

    def _get_Children(self):
        return self.getChildren()

    def _get_ColorizableTexts(self):
        return self.getColorizableTexts()

    def _set_ColorizableTexts(self, src):
        return self.setColorizableTexts(src)
