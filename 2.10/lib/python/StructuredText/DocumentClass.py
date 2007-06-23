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

from zope.structuredtext.document import Document as DocumentClass
from zope.structuredtext.stng import (
    StructuredTextExample, StructuredTextBullet, StructuredTextNumbered,
    StructuredTextDescriptionTitle, StructuredTextDescriptionBody,
    StructuredTextDescription, StructuredTextSectionTitle,
    StructuredTextSection, StructuredTextTable, StructuredTextRow,
    StructuredTextColumn, StructuredTextTableHeader,
    StructuredTextTableData, StructuredTextMarkup, StructuredTextLiteral,
    StructuredTextEmphasis, StructuredTextStrong, StructuredTextInnerLink,
    StructuredTextNamedLink, StructuredTextUnderline, StructuredTextSGML,
    StructuredTextLink, StructuredTextXref
    )

from zope.deprecation import deprecated
deprecated("DocumentClass",
           'The StructuredText package is deprecated and will be removed '
           'in Zope 2.12. Use zope.structuredtext.document.Document '
           'instead.')
