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

""" Alias module for StructuredTextClassic compatibility which makes
use of StructuredTextNG """


import HTMLClass, DocumentClass 
import DocumentWithImages, HTMLWithImages
from ST import Basic

import re, sys
from STletters import letters

Document = DocumentClass.DocumentClass()
HTMLNG = HTMLClass.HTMLClass()

DocumentImages = DocumentWithImages.DocumentWithImages()
HTMLNGImages = HTMLWithImages.HTMLWithImages()

def HTML(aStructuredString, level=1, header=1):
    st = Basic(aStructuredString)
    doc = DocumentImages(st)
    return HTMLNGImages(doc,header=header,level=level)

def StructuredText(aStructuredString, level=1):
    return HTML(aStructuredString,level)

def html_with_references(text, level=1, header=1):
    text = re.sub(
        r'[\000\n]\.\. \[([0-9_%s-]+)\]' % letters,
        r'\n  <a name="\1">[\1]</a>',
        text)

    text = re.sub(
        r'([\000- ,])\[(?P<ref>[0-9_%s-]+)\]([\000- ,.:])'   % letters,
        r'\1<a href="#\2">[\2]</a>\3',
        text)

    text = re.sub(
        r'([\000- ,])\[([^]]+)\.html\]([\000- ,.:])',
        r'\1<a href="\2.html">[\2]</a>\3',
        text)

    return HTML(text,level=level,header=header)

def html_quote(v,
               character_entities=(
                       (re.compile('&'), '&amp;'),
                       (re.compile("<"), '&lt;' ),
                       (re.compile(">"), '&gt;' ),
                       (re.compile('"'), '&quot;')
                       )): #"
    text=str(v)
    for re,name in character_entities:
        text=re.sub(name,text)
    return text


if __name__=='__main__':
    import getopt

    opts,args = getopt.getopt(sys.argv[1:],'',[])

    for k,v in opts:
        pass


    for f in args:
        print HTML(open(f).read())
