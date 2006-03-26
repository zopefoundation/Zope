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

from zope.structuredtext import html, document, docbook
from zope.structuredtext.stng import structurize as Basic

from StructuredText import html_quote
from zope.structuredtext import stx2html as HTML
from zope.structuredtext import stx2htmlWithReferences as html_with_references
from types import StringType, UnicodeType

# BBB -- 2006/01/08 -- Remove in Zope 2.12
import sys
import zope.structuredtext.stletters
import zope.structuredtext.stdom
sys.modules['StructuredText.STletters'] = zope.structuredtext.stletters
sys.modules['StructuredText.STDOM'] = zope.structuredtext.stdom

import ClassicDocumentClass
Classic = ClassicDocumentClass.DocumentClass()
Document = document.Document()
DocumentWithImages = document.DocumentWithImages()
HTMLWithImages = html.HTMLWithImages()
ClassicHTML = html.HTML
HTMLNG = html.HTML()

DocBookBook = docbook.DocBookBook()
DocBookChapter = docbook.DocBookChapter()
DocBookChapterWithFigures = docbook.DocBookChapterWithFigures()
DocBookArticle = docbook.DocBookArticle()

def HTML(src, level=1):
    import warnings
    warnings.warn(
        'The StructuredText package is deprecated and will be removed '
        'in Zope 2.12. Use zope.structuredtext instead.',
        DeprecationWarning, stacklevel=2)
    if isinstance(src, basestring):
        return ClassicHTML(src, level)
    return HTMLNG(src, level)
