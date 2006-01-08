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

from zope.structuredtext.docbook import DocBook as DocBookClass
from zope.structuredtext.docbook import \
     DocBookChapter, DocBookChapterWithFigures, DocBookArticle, DocBookBook

from zope.deprecation import deprecated
deprecated("DocBookClass",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.docbook.DocBook '
           'instead.')
deprecated("DocBookChapter",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.docbook.DocBookChapter '
           'instead.')
deprecated("DocBookChapterWithFigures",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.docbook.DocBookChapterWithFigures '
           'instead.')
deprecated("DocBookArticle",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.docbook.DocBookArticle '
           'instead.')
deprecated("DocBookBook",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.docbook.DocBookBook '
           'instead.')
