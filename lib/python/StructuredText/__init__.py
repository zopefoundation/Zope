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

import HTMLClass, DocumentClass
import ClassicDocumentClass
from StructuredText import html_with_references, HTML, html_quote
from ST import Basic
import DocBookClass
import HTMLWithImages
from types import StringType, UnicodeType
import DocumentWithImages

ClassicHTML=HTML
HTMLNG=HTMLClass.HTMLClass()

def HTML(src, level=1):
    if isinstance(src, StringType) or isinstance(src, UnicodeType):
        return ClassicHTML(src, level)
    return HTMLNG(src, level)

Classic=ClassicDocumentClass.DocumentClass()
Document=DocumentClass.DocumentClass()
DocumentWithImages=DocumentWithImages.DocumentWithImages()
HTMLWithImages=HTMLWithImages.HTMLWithImages()

DocBookBook=DocBookClass.DocBookBook()
DocBookChapter=DocBookClass.DocBookChapter()
DocBookChapterWithFigures=DocBookClass.DocBookChapterWithFigures()
DocBookArticle=DocBookClass.DocBookArticle()
